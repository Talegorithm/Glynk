"""
Resonote → Glynk 数据迁移

在服务器上的 Glynk API 容器内运行：
  docker-compose exec api python3 scripts/migrate_from_resonote.py

前提：
  - resonote-pg-readonly 容器已启动并连入 glynk_glynk 网络
  - Glynk PostgreSQL 已启动
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import logging

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# ===== 配置 =====

# Resonote 数据源（通过 Docker 网络连接临时容器）
SRC_HOST = os.getenv("RESONOTE_PG_HOST", "resonote-pg-readonly")
SRC_PORT = int(os.getenv("RESONOTE_PG_PORT", "5432"))
SRC_USER = os.getenv("RESONOTE_PG_USER", "resonote")
SRC_PASS = os.getenv("RESONOTE_PG_PASS", "resonote_pass")
SRC_DB = os.getenv("RESONOTE_PG_DB", "resonote_library")
SRC_HTML = Path(os.getenv("RESONOTE_HTML_ROOT", "/mnt/tracker/Resonote/Resonote-data/library_html"))

# Glynk 目标
DST_HOST = os.getenv("POSTGRES_HOST", "postgres")
DST_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DST_USER = os.getenv("POSTGRES_USER", "glynk")
DST_PASS = os.getenv("POSTGRES_PASSWORD", "glynk")
DST_DB = os.getenv("POSTGRES_DB", "glynk")
DST_HTML = Path(os.getenv("DATA_ROOT", "/data")) / "html"

# 备份
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/mnt/tracker/Resonote/backup"))


def connect(host, port, user, password, dbname):
    return psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname)


def step1_backup():
    """备份 Resonote 数据为 JSON"""
    log.info("\n" + "=" * 50)
    log.info("Step 1: 备份 Resonote 数据")
    log.info("=" * 50)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    conn = connect(SRC_HOST, SRC_PORT, SRC_USER, SRC_PASS, SRC_DB)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    for table in ['contents', 'highlights', 'questions']:
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        for row in rows:
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    row[k] = v.isoformat()
        out_file = backup_path / f"{table}.json"
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, default=str)
        log.info(f"  {table}: {len(rows)} rows → {out_file.name}")

    conn.close()
    log.info(f"  Backup: {backup_path}")
    return backup_path


def step2_migrate():
    """迁移 EPUB + 已分析 web_article 到 Glynk"""
    log.info("\n" + "=" * 50)
    log.info("Step 2: 迁移数据到 Glynk")
    log.info("=" * 50)

    src = connect(SRC_HOST, SRC_PORT, SRC_USER, SRC_PASS, SRC_DB)
    dst = connect(DST_HOST, DST_PORT, DST_USER, DST_PASS, DST_DB)
    src_cur = src.cursor(cursor_factory=RealDictCursor)
    dst_cur = dst.cursor()

    # --- 2a: 迁移 contents ---
    log.info("\n  [contents] 迁移 EPUB + 已分析 web_article...")
    src_cur.execute("""
        SELECT * FROM contents
        WHERE (type = 'epub' AND status = 'analyzed')
           OR (type = 'web_article' AND status = 'analyzed')
        ORDER BY created_at
    """)
    contents = src_cur.fetchall()
    log.info(f"  Found {len(contents)} contents to migrate")

    migrated_ids = []
    skipped = 0
    for c in contents:
        content_id = c['id']

        # 去重
        dst_cur.execute("SELECT 1 FROM contents WHERE content_id = %s", (content_id,))
        if dst_cur.fetchone():
            skipped += 1
            migrated_ids.append(content_id)
            continue

        # 计算 file_count
        html_dir = SRC_HTML / content_id
        file_count = len(list(html_dir.glob("*.html"))) if html_dir.exists() else 0

        # 映射 source_type
        source_type_map = {'epub': 'epub', 'web_article': 'url', 'pdf': 'pdf'}
        source_type = source_type_map.get(c.get('type', ''), c.get('type', 'generic'))

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
            source_type,
            c.get('source_url'),
            c.get('source_file_hash', content_id),
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
        migrated_ids.append(content_id)

    dst.commit()
    log.info(f"  Migrated: {len(migrated_ids) - skipped} new, {skipped} skipped (already exist)")

    # --- 2b: 迁移 highlights → annotations ---
    log.info("\n  [highlights → annotations] ...")
    src_cur.execute("""
        SELECT * FROM highlights
        WHERE content_id = ANY(%s) AND owner_uid IS NULL
        ORDER BY created_at
    """, (migrated_ids,))
    highlights = src_cur.fetchall()
    log.info(f"  Found {len(highlights)} highlights")

    hl_new = 0
    for h in highlights:
        ann_id = f"ann-{h['id'].replace('highlight-', '')[:12]}"

        dst_cur.execute("SELECT 1 FROM annotations WHERE id = %s", (ann_id,))
        if dst_cur.fetchone():
            continue

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
            [h.get('type', 'Insight')],
            h.get('contextuality', 'standalone'),
            'agent', None, 'public',
            h.get('created_at'),
        ))
        hl_new += 1

    dst.commit()
    log.info(f"  Highlights migrated: {hl_new}")

    # --- 2c: 迁移 questions → annotations (type=hook) ---
    log.info("\n  [questions → annotations (hook)] ...")
    src_cur.execute("""
        SELECT * FROM questions
        WHERE content_id = ANY(%s) AND owner_uid IS NULL
        ORDER BY created_at
    """, (migrated_ids,))
    questions = src_cur.fetchall()
    log.info(f"  Found {len(questions)} questions")

    q_new = 0
    for q in questions:
        ann_id = f"ann-{q['id'].replace('question-', '')[:12]}"

        dst_cur.execute("SELECT 1 FROM annotations WHERE id = %s", (ann_id,))
        if dst_cur.fetchone():
            continue

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
            'agent', None, 'public',
            q.get('created_at'),
        ))
        q_new += 1

    dst.commit()
    log.info(f"  Questions→hooks migrated: {q_new}")

    src.close()
    dst.close()
    return migrated_ids


def step3_copy_html(content_ids: list):
    """复制 HTML 文件"""
    log.info("\n" + "=" * 50)
    log.info("Step 3: 复制 HTML 文件")
    log.info("=" * 50)

    DST_HTML.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0
    missing = 0
    for cid in content_ids:
        src_dir = SRC_HTML / cid
        dst_dir = DST_HTML / cid

        if not src_dir.exists():
            missing += 1
            continue

        if dst_dir.exists():
            skipped += 1
            continue

        shutil.copytree(src_dir, dst_dir)
        copied += 1

    log.info(f"  Copied: {copied}, Skipped: {skipped}, Missing: {missing}")


def main():
    log.info("=" * 50)
    log.info("  Resonote → Glynk 数据迁移")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 50)
    log.info(f"  Source: {SRC_HOST}:{SRC_PORT}/{SRC_DB}")
    log.info(f"  Target: {DST_HOST}:{DST_PORT}/{DST_DB}")
    log.info(f"  HTML:   {SRC_HTML} → {DST_HTML}")

    backup_path = step1_backup()
    content_ids = step2_migrate()
    step3_copy_html(content_ids)

    log.info("\n" + "=" * 50)
    log.info(f"  迁移完成! {len(content_ids)} contents")
    log.info(f"  备份: {backup_path}")
    log.info("=" * 50)


if __name__ == "__main__":
    main()
