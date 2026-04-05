"""
Resonote → Glynk 数据迁移

在服务器上运行：
  python3 scripts/migrate_from_resonote.py

做三件事：
  1. 备份 Resonote 的 PostgreSQL 数据
  2. 将 EPUB 内容 + highlights + questions 迁移到 Glynk schema
  3. 复制 HTML 文件到 Glynk 数据目录

前提条件：
  - Resonote 的 PostgreSQL 可访问（通过 docker exec 或直连）
  - Glynk 的 PostgreSQL 已启动（docker-compose up postgres）
  - 两边的数据目录可访问
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# ===== 配置 =====

# Resonote 数据源
RESONOTE_PG_HOST = os.getenv("RESONOTE_PG_HOST", "localhost")
RESONOTE_PG_PORT = os.getenv("RESONOTE_PG_PORT", "22233")
RESONOTE_PG_USER = os.getenv("RESONOTE_PG_USER", "resonote")
RESONOTE_PG_PASS = os.getenv("RESONOTE_PG_PASS", "resonote_pass")
RESONOTE_PG_DB = os.getenv("RESONOTE_PG_DB", "resonote_track")
RESONOTE_HTML_ROOT = Path(os.getenv("RESONOTE_HTML_ROOT", "/mnt/tracker/Resonote/Resonote-data/library_html"))

# Glynk 目标
GLYNK_PG_HOST = os.getenv("GLYNK_PG_HOST", "localhost")
GLYNK_PG_PORT = os.getenv("GLYNK_PG_PORT", "22433")
GLYNK_PG_USER = os.getenv("GLYNK_PG_USER", "glynk")
GLYNK_PG_PASS = os.getenv("GLYNK_PG_PASS", "glynk")
GLYNK_PG_DB = os.getenv("GLYNK_PG_DB", "glynk")
GLYNK_HTML_ROOT = Path(os.getenv("GLYNK_HTML_ROOT", "/mnt/tracker/Glynk/Glynk-data/html"))

# 备份目录
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/mnt/tracker/Resonote/backup"))


def connect_pg(host, port, user, password, dbname):
    import psycopg2
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)
    return conn


def step1_backup():
    """Step 1: 备份 Resonote PostgreSQL"""
    print("\n" + "=" * 50)
    print("Step 1: 备份 Resonote 数据")
    print("=" * 50)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    # pg_dump
    dump_file = backup_path / "resonote_pg.sql"
    print(f"  Dumping PostgreSQL → {dump_file}")

    env = os.environ.copy()
    env["PGPASSWORD"] = RESONOTE_PG_PASS
    result = subprocess.run([
        "pg_dump",
        "-h", RESONOTE_PG_HOST,
        "-p", RESONOTE_PG_PORT,
        "-U", RESONOTE_PG_USER,
        "-d", RESONOTE_PG_DB,
        "--table=contents",
        "--table=highlights",
        "--table=questions",
        "--table=leaves",
        "-f", str(dump_file),
    ], env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  WARNING: pg_dump failed: {result.stderr}")
        print(f"  Trying direct query backup...")
        _backup_via_query(backup_path)
    else:
        print(f"  pg_dump OK: {dump_file.stat().st_size:,} bytes")

    print(f"  Backup saved to: {backup_path}")
    return backup_path


def _backup_via_query(backup_path: Path):
    """pg_dump 不可用时，通过查询导出 JSON"""
    conn = connect_pg(RESONOTE_PG_HOST, int(RESONOTE_PG_PORT),
                      RESONOTE_PG_USER, RESONOTE_PG_PASS, RESONOTE_PG_DB)
    cur = conn.cursor(cursor_factory=__import__('psycopg2.extras', fromlist=['RealDictCursor']).RealDictCursor)

    for table in ['contents', 'highlights', 'questions']:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        # Convert datetime to string for JSON
        for row in rows:
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()
        out_file = backup_path / f"{table}.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
        print(f"  Exported {table}: {len(rows)} rows → {out_file.name}")

    conn.close()


def step2_migrate():
    """Step 2: 迁移数据到 Glynk"""
    print("\n" + "=" * 50)
    print("Step 2: 迁移数据到 Glynk")
    print("=" * 50)

    # 连接两个数据库
    src = connect_pg(RESONOTE_PG_HOST, int(RESONOTE_PG_PORT),
                     RESONOTE_PG_USER, RESONOTE_PG_PASS, RESONOTE_PG_DB)
    dst = connect_pg(GLYNK_PG_HOST, int(GLYNK_PG_PORT),
                     GLYNK_PG_USER, GLYNK_PG_PASS, GLYNK_PG_DB)

    from psycopg2.extras import RealDictCursor, Json
    src_cur = src.cursor(cursor_factory=RealDictCursor)
    dst_cur = dst.cursor()

    # --- 2a: 迁移 contents（只迁移 EPUB，跳过 RSS 垃圾数据）---
    print("\n  [contents] 迁移 EPUB 内容...")
    src_cur.execute("""
        SELECT * FROM contents
        WHERE type = 'epub' AND status IN ('parsed', 'analyzed')
        ORDER BY created_at
    """)
    contents = src_cur.fetchall()
    print(f"  Found {len(contents)} EPUB contents")

    migrated_content_ids = []
    for c in contents:
        content_id = c['id']

        # 检查是否已迁移
        dst_cur.execute("SELECT 1 FROM contents WHERE content_id = %s", (content_id,))
        if dst_cur.fetchone():
            print(f"    Skip (exists): {content_id} {c.get('current_title', '')[:30]}")
            migrated_content_ids.append(content_id)
            continue

        # 计算 file_count
        html_dir = RESONOTE_HTML_ROOT / content_id
        file_count = len(list(html_dir.glob("*.html"))) if html_dir.exists() else 0

        dst_cur.execute("""
            INSERT INTO contents (content_id, title, author, source_type, source_url,
                source_file_hash, file_count, toc_json, ai_outline_json, abstract,
                uid, status, total_chars, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (content_id) DO NOTHING
        """, (
            content_id,
            c.get('current_title') or c.get('original_title', ''),
            c.get('current_author') or c.get('original_author', 'Unknown'),
            c.get('type', 'epub'),
            c.get('source_url'),
            c.get('source_file_hash', ''),
            file_count,
            c.get('toc_json', '[]'),
            c.get('outline_json', '[]'),
            c.get('abstract', ''),
            c.get('uploader_uid'),
            'ready',
            c.get('total_chars', 0),
            c.get('created_at'),
            c.get('updated_at'),
        ))
        migrated_content_ids.append(content_id)
        print(f"    Migrated: {content_id} {c.get('current_title', '')[:40]}")

    dst.commit()
    print(f"  Contents migrated: {len(migrated_content_ids)}")

    # --- 2b: 迁移 highlights → annotations ---
    print("\n  [highlights → annotations] 迁移高亮...")
    src_cur.execute("""
        SELECT * FROM highlights
        WHERE content_id = ANY(%s) AND owner_uid IS NULL
        ORDER BY created_at
    """, (migrated_content_ids,))
    highlights = src_cur.fetchall()
    print(f"  Found {len(highlights)} highlights")

    hl_count = 0
    for h in highlights:
        ann_id = f"ann-{h['id'].replace('highlight-', '')[:12]}"
        location = h.get('location', [])
        if isinstance(location, str):
            location = json.loads(location)

        dst_cur.execute("""
            INSERT INTO annotations (id, content_id, anchor, type, text, tags,
                contextuality, source, uid, visibility, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            ann_id,
            h['content_id'],
            Json({"type": "text", "spans": location}),
            'highlight',
            h.get('text', ''),
            [h.get('type', 'Insight')],  # Emotion/Insight/Instruction → tag
            h.get('contextuality', 'standalone'),
            'agent',
            None,  # 通用分析，不属于特定用户
            'public',
            h.get('created_at'),
        ))
        hl_count += 1

    dst.commit()
    print(f"  Highlights migrated: {hl_count}")

    # --- 2c: 迁移 questions → annotations (type=hook) ---
    print("\n  [questions → annotations] 迁移问题...")
    src_cur.execute("""
        SELECT * FROM questions
        WHERE content_id = ANY(%s) AND owner_uid IS NULL
        ORDER BY created_at
    """, (migrated_content_ids,))
    questions = src_cur.fetchall()
    print(f"  Found {len(questions)} questions")

    q_count = 0
    for q in questions:
        ann_id = f"ann-{q['id'].replace('question-', '')[:12]}"
        location = q.get('location', [])
        if isinstance(location, str):
            location = json.loads(location)

        keywords = q.get('keywords', [])
        if isinstance(keywords, str):
            keywords = json.loads(keywords)
        topics = q.get('topics', [])
        if isinstance(topics, str):
            topics = json.loads(topics)

        dst_cur.execute("""
            INSERT INTO annotations (id, content_id, anchor, type, text, tags,
                contextuality, source, uid, visibility, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            ann_id,
            q['content_id'],
            Json({"type": "text", "spans": location}),
            'hook',
            q.get('question', ''),
            keywords + topics,
            q.get('contextuality', 'standalone'),
            'agent',
            None,
            'public',
            q.get('created_at'),
        ))
        q_count += 1

    dst.commit()
    print(f"  Questions→hooks migrated: {q_count}")

    src.close()
    dst.close()

    return migrated_content_ids


def step3_copy_html(content_ids: list):
    """Step 3: 复制 HTML 文件"""
    print("\n" + "=" * 50)
    print("Step 3: 复制 HTML 文件")
    print("=" * 50)

    GLYNK_HTML_ROOT.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    for cid in content_ids:
        src_dir = RESONOTE_HTML_ROOT / cid
        dst_dir = GLYNK_HTML_ROOT / cid

        if not src_dir.exists():
            print(f"  Skip (no HTML): {cid}")
            skipped += 1
            continue

        if dst_dir.exists():
            # 已存在，跳过
            skipped += 1
            continue

        shutil.copytree(src_dir, dst_dir)
        file_count = len(list(dst_dir.glob("*.html")))
        print(f"  Copied: {cid} ({file_count} files)")
        copied += 1

    print(f"  Copied: {copied}, Skipped: {skipped}")


def main():
    print("=" * 50)
    print("  Resonote → Glynk 数据迁移")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    print(f"  Source: {RESONOTE_PG_HOST}:{RESONOTE_PG_PORT}/{RESONOTE_PG_DB}")
    print(f"  Target: {GLYNK_PG_HOST}:{GLYNK_PG_PORT}/{GLYNK_PG_DB}")
    print(f"  HTML:   {RESONOTE_HTML_ROOT} → {GLYNK_HTML_ROOT}")

    # Step 1: 备份
    backup_path = step1_backup()

    # Step 2: 迁移
    content_ids = step2_migrate()

    # Step 3: 复制 HTML
    step3_copy_html(content_ids)

    print("\n" + "=" * 50)
    print("  迁移完成!")
    print(f"  备份: {backup_path}")
    print(f"  内容: {len(content_ids)} items")
    print("=" * 50)


if __name__ == "__main__":
    main()
