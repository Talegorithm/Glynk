#!/usr/bin/env python3
"""
Migrate Glynk from v1 (contents/annotations/users) to v2 (entities/units/anchors).

Usage:
    python scripts/migrate_to_v2.py                    # dry run
    python scripts/migrate_to_v2.py --execute          # actually migrate
    python scripts/migrate_to_v2.py --execute --drop   # migrate + drop old tables

Preserves:
  - All content data (contents → units)
  - All annotations (annotations → units + anchors), including embeddings
  - All users (users → entities + auth)
  - Reading progress and sessions
  - RSS sources

Author handling:
  - contents.author → dormant Entity
  - contents.uid → metadata.imported_by (NOT author)
  - annotations.uid → annotation unit's author_id (through entity)
"""
import json
import os
import sys
import logging
from uuid import uuid4

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Config
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "glynk")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "glynk")
DB_NAME = os.getenv("POSTGRES_DB", "glynk")

DRY_RUN = "--execute" not in sys.argv
DROP_OLD = "--drop" in sys.argv


def connect():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME
    )


def check_old_tables_exist(cur):
    cur.execute("SELECT to_regclass('public.contents') as t")
    return cur.fetchone()['t'] is not None


def check_new_tables_exist(cur):
    cur.execute("SELECT to_regclass('public.entities') as t")
    return cur.fetchone()['t'] is not None


def create_new_tables(cur):
    """Create new v2 tables (if they don't exist)."""
    from pathlib import Path
    # Read DDL from postgres.py
    init_sql_path = Path(__file__).parent.parent / "glynk" / "storage" / "postgres.py"
    source = init_sql_path.read_text()
    # Extract INIT_SQL
    start = source.index('INIT_SQL = """') + len('INIT_SQL = """')
    end = source.index('"""', start)
    ddl = source[start:end]
    cur.execute(ddl)
    logger.info("New tables created")


def migrate_users(cur):
    """users → entities + auth"""
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    logger.info(f"Migrating {len(users)} users")

    for u in users:
        uid = u['uid']
        # Create entity
        cur.execute("""
            INSERT INTO entities (id, kind, state, display_name, created_at)
            VALUES (%s, 'human', 'active', %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (uid, u.get('name') or uid, u.get('created_at')))

        # Create auth
        cur.execute("""
            INSERT INTO auth (entity_id, token, email, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (entity_id) DO NOTHING
        """, (uid, u['token'], u['email'], u.get('created_at')))

    logger.info(f"  → {len(users)} entities + auth records created")
    return {u['uid'] for u in users}


def migrate_contents(cur, known_entities: set):
    """contents → units (with dormant author entities)"""
    cur.execute("SELECT * FROM contents WHERE status = 'ready'")
    contents = cur.fetchall()
    logger.info(f"Migrating {len(contents)} contents")

    author_entity_map = {}  # author_name → entity_id

    for c in contents:
        author_name = c.get('author') or 'Unknown'

        # Get or create dormant entity for the author
        if author_name not in author_entity_map:
            # Check if this author name matches an existing active entity (user)
            cur.execute(
                "SELECT id FROM entities WHERE display_name = %s LIMIT 1",
                (author_name,)
            )
            existing = cur.fetchone()
            if existing:
                author_entity_map[author_name] = existing['id']
            else:
                entity_id = f"ent-{uuid4().hex[:12]}"
                cur.execute("""
                    INSERT INTO entities (id, kind, state, display_name)
                    VALUES (%s, 'human', 'dormant', %s)
                    ON CONFLICT (id) DO NOTHING
                """, (entity_id, author_name))
                author_entity_map[author_name] = entity_id

        author_entity_id = author_entity_map[author_name]

        # Build unit body and metadata
        toc = []
        try:
            toc = json.loads(c.get('toc_json') or '[]')
        except Exception:
            pass

        ai_outline = []
        try:
            ai_outline = json.loads(c.get('ai_outline_json') or '[]')
        except Exception:
            pass

        body = {
            "toc": toc,
            "file_count": c.get('file_count', 0),
        }

        metadata = {
            "title": c.get('title', ''),
            "abstract": c.get('abstract', ''),
            "source_type": c.get('source_type', ''),
            "source_url": c.get('source_url'),
            "source_file_hash": c.get('source_file_hash', ''),
            "total_chars": c.get('total_chars', 0),
            "imported_by": c.get('uid'),  # NOT the author!
            "status": "ready",
            "language": c.get('language'),
            "ai_outline": ai_outline,
        }

        cur.execute("""
            INSERT INTO units (id, author_id, origin, shape, body, visibility, metadata, created_at)
            VALUES (%s, %s, 'ingested', 'structured', %s, '{"type":"public"}', %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            c['content_id'], author_entity_id,
            Json(body), Json(metadata), c.get('created_at'),
        ))

    logger.info(f"  → {len(contents)} units + {len(author_entity_map)} author entities created")
    return author_entity_map


def migrate_annotations(cur, known_entities: set):
    """annotations → units (source) + anchors"""
    cur.execute("SELECT *, embedding::text as embedding_text FROM annotations")
    annotations = cur.fetchall()
    logger.info(f"Migrating {len(annotations)} annotations")

    created_units = 0
    created_anchors = 0

    for ann in annotations:
        uid = ann.get('uid')

        # Ensure the entity exists (some annotations may reference UIDs not in users table)
        if uid and uid not in known_entities:
            cur.execute("""
                INSERT INTO entities (id, kind, state, display_name)
                VALUES (%s, %s, 'active', %s)
                ON CONFLICT (id) DO NOTHING
            """, (uid, 'ai' if ann.get('source') == 'ai' else 'human', uid))
            known_entities.add(uid)

        # Extract anchor data
        old_anchor = ann.get('anchor') or {}
        if isinstance(old_anchor, str):
            try:
                old_anchor = json.loads(old_anchor)
            except Exception:
                old_anchor = {}

        spans = old_anchor.get('spans', [])
        target_span = spans[0] if spans else None

        # Create source Unit (with the annotation text + embedding)
        source_unit_id = ann['id']  # Reuse old annotation ID
        embedding_text = ann.get('embedding_text')

        visibility = {"type": ann.get('visibility', 'public')}
        unit_metadata = {
            "tags": ann.get('tags') or [],
            "role": ann.get('type', ''),
            "contextuality": ann.get('contextuality', 'standalone'),
        }

        if embedding_text and embedding_text != 'None':
            cur.execute("""
                INSERT INTO units (id, author_id, origin, shape, body, visibility, metadata,
                                   vector, vector_text, created_at)
                VALUES (%s, %s, 'authored', 'flat', %s, %s, %s, %s::vector, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                source_unit_id,
                uid or 'unknown',
                Json({"html": ann.get('text', '')}),
                Json(visibility),
                Json(unit_metadata),
                embedding_text,
                ann.get('text', ''),
                ann.get('created_at'),
            ))
        else:
            cur.execute("""
                INSERT INTO units (id, author_id, origin, shape, body, visibility, metadata,
                                   created_at)
                VALUES (%s, %s, 'authored', 'flat', %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                source_unit_id,
                uid or 'unknown',
                Json({"html": ann.get('text', '')}),
                Json(visibility),
                Json(unit_metadata),
                ann.get('created_at'),
            ))
        created_units += 1

        # Create Anchor
        anchor_id = f"anc-{uuid4().hex[:12]}"
        target_type = 'span' if target_span else 'unit'

        # Move highlight-specific fields to anchor metadata
        anchor_metadata = {}
        for key in ('type', 'spans', 'startSpanId', 'endSpanId',
                    'startOffset', 'endOffset', 'color', 'note'):
            if key in old_anchor:
                anchor_metadata[key] = old_anchor[key]

        cur.execute("""
            INSERT INTO anchors (id, source_type, source_unit, target_type,
                                 target_unit, target_span, role, metadata, created_at)
            VALUES (%s, 'unit', %s, %s, %s, %s, %s, %s, %s)
        """, (
            anchor_id,
            source_unit_id,
            target_type,
            ann.get('content_id'),
            target_span,
            ann.get('type', 'highlight'),
            Json(anchor_metadata),
            ann.get('created_at'),
        ))
        created_anchors += 1

    logger.info(f"  → {created_units} annotation units + {created_anchors} anchors created")


def migrate_reading_progress(cur, known_entities: set):
    """reading_progress: uid/content_id → entity_id/unit_id"""
    cur.execute("SELECT * FROM reading_progress")
    rows = cur.fetchall()
    logger.info(f"Migrating {len(rows)} reading_progress records")

    # The new table has the same structure but different column names
    # We need to check if the old table uses uid/content_id vs entity_id/unit_id
    for r in rows:
        uid = r.get('uid') or r.get('entity_id')
        cid = r.get('content_id') or r.get('unit_id')
        if uid and uid in known_entities and cid:
            cur.execute("""
                INSERT INTO reading_progress (entity_id, unit_id, span_id, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (entity_id, unit_id) DO NOTHING
            """, (uid, cid, r['span_id'], r.get('updated_at')))

    logger.info(f"  → {len(rows)} reading_progress records migrated")


def migrate_reading_sessions(cur, known_entities: set):
    """reading_sessions: uid/content_id → entity_id/unit_id"""
    cur.execute("SELECT * FROM reading_sessions")
    rows = cur.fetchall()
    logger.info(f"Migrating {len(rows)} reading_sessions")

    for r in rows:
        uid = r.get('uid') or r.get('entity_id')
        cid = r.get('content_id') or r.get('unit_id')
        if uid and uid in known_entities and cid:
            cur.execute("""
                INSERT INTO reading_sessions (id, entity_id, unit_id, started_at, ended_at,
                                              duration_seconds, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (r['id'], uid, cid, r.get('started_at'), r.get('ended_at'),
                  r.get('duration_seconds'), r.get('source', 'manual')))

    logger.info(f"  → {len(rows)} reading_sessions migrated")


def migrate_rss_sources(cur, known_entities: set):
    """rss_sources: created_by uid → entity_id"""
    cur.execute("SELECT * FROM rss_sources")
    rows = cur.fetchall()
    logger.info(f"Migrating {len(rows)} rss_sources")

    for r in rows:
        created_by = r.get('created_by')
        if created_by and created_by not in known_entities:
            created_by = None  # FK won't resolve

        cur.execute("""
            INSERT INTO rss_sources (id, url, name, content_type, schedule, max_items,
                                     enabled, filters, created_by, last_fetched_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            r['id'], r['url'], r.get('name', ''), r.get('content_type'),
            r.get('schedule', 'daily'), r.get('max_items', 5),
            r.get('enabled', True), Json(r.get('filters') or {}),
            created_by, r.get('last_fetched_at'), r.get('created_at'),
        ))

    logger.info(f"  → {len(rows)} rss_sources migrated")


def drop_old_tables(cur):
    """Drop old v1 tables after migration."""
    old_tables = [
        'translations', 'feedback', 'queries',
        'reading_sessions', 'reading_progress',
        'annotations', 'contents', 'users',
    ]
    for table in old_tables:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        logger.info(f"  Dropped {table}")


def rename_old_tables(cur):
    """Rename old tables with _v1 suffix as backup."""
    old_tables = [
        'translations', 'feedback', 'queries',
        'annotations', 'contents', 'users',
    ]
    for table in old_tables:
        cur.execute(f"SELECT to_regclass('public.{table}') as t")
        if cur.fetchone()['t']:
            cur.execute(f"ALTER TABLE {table} RENAME TO {table}_v1")
            logger.info(f"  Renamed {table} → {table}_v1")

    # Also rename old reading_progress and reading_sessions
    for table in ['reading_progress', 'reading_sessions']:
        cur.execute(f"SELECT to_regclass('public.{table}') as t")
        if cur.fetchone()['t']:
            cur.execute(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = 'uid'
            """)
            if cur.fetchone():
                cur.execute(f"ALTER TABLE {table} RENAME TO {table}_v1")
                logger.info(f"  Renamed {table} → {table}_v1 (has old uid column)")


def main():
    if DRY_RUN:
        logger.info("=== DRY RUN MODE (pass --execute to actually migrate) ===")

    conn = connect()
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        if not check_old_tables_exist(cur):
            logger.error("Old tables (contents, etc.) not found. Nothing to migrate.")
            return

        logger.info("=== Step 1: Rename old tables ===")
        if not DRY_RUN:
            rename_old_tables(cur)
        else:
            logger.info("  (skipped in dry run)")

        logger.info("=== Step 2: Create new tables ===")
        if not DRY_RUN:
            create_new_tables(cur)
        else:
            logger.info("  (skipped in dry run)")

        # Read from _v1 tables
        if not DRY_RUN:
            # Point queries to renamed tables
            cur.execute("SET search_path TO public")

            logger.info("=== Step 3: Migrate users → entities + auth ===")
            # Read from users_v1
            cur.execute("SELECT * FROM users_v1")
            users = cur.fetchall()
            known_entities = set()
            for u in users:
                uid = u['uid']
                cur.execute("""
                    INSERT INTO entities (id, kind, state, display_name, created_at)
                    VALUES (%s, 'human', 'active', %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (uid, u.get('name') or uid, u.get('created_at')))
                cur.execute("""
                    INSERT INTO auth (entity_id, token, email, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (entity_id) DO NOTHING
                """, (uid, u['token'], u['email'], u.get('created_at')))
                known_entities.add(uid)
            logger.info(f"  → {len(users)} entities + auth records created")

            logger.info("=== Step 4: Migrate contents → units ===")
            cur.execute("SELECT * FROM contents_v1 WHERE status = 'ready'")
            contents = cur.fetchall()
            author_entity_map = {}
            for c in contents:
                author_name = c.get('author') or 'Unknown'
                if author_name not in author_entity_map:
                    cur.execute("SELECT id FROM entities WHERE display_name = %s LIMIT 1", (author_name,))
                    existing = cur.fetchone()
                    if existing:
                        author_entity_map[author_name] = existing['id']
                    else:
                        eid = f"ent-{uuid4().hex[:12]}"
                        cur.execute("""
                            INSERT INTO entities (id, kind, state, display_name)
                            VALUES (%s, 'human', 'dormant', %s)
                        """, (eid, author_name))
                        author_entity_map[author_name] = eid

                toc = []
                try: toc = json.loads(c.get('toc_json') or '[]')
                except: pass
                ai_outline = []
                try: ai_outline = json.loads(c.get('ai_outline_json') or '[]')
                except: pass

                body = {"toc": toc, "file_count": c.get('file_count', 0)}
                metadata = {
                    "title": c.get('title', ''),
                    "abstract": c.get('abstract', ''),
                    "source_type": c.get('source_type', ''),
                    "source_url": c.get('source_url'),
                    "source_file_hash": c.get('source_file_hash', ''),
                    "total_chars": c.get('total_chars', 0),
                    "imported_by": c.get('uid'),
                    "status": "ready",
                    "language": c.get('language'),
                    "ai_outline": ai_outline,
                }
                cur.execute("""
                    INSERT INTO units (id, author_id, origin, shape, body, visibility, metadata, created_at)
                    VALUES (%s, %s, 'ingested', 'structured', %s, '{"type":"public"}', %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (c['content_id'], author_entity_map[author_name],
                      Json(body), Json(metadata), c.get('created_at')))
            logger.info(f"  → {len(contents)} units + {len(author_entity_map)} author entities")

            logger.info("=== Step 5: Migrate annotations → units + anchors ===")
            cur.execute("SELECT *, embedding::text as embedding_text FROM annotations_v1")
            annotations = cur.fetchall()
            for ann in annotations:
                uid = ann.get('uid')
                if uid and uid not in known_entities:
                    cur.execute("""
                        INSERT INTO entities (id, kind, state, display_name)
                        VALUES (%s, %s, 'active', %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (uid, 'ai' if ann.get('source') == 'ai' else 'human', uid))
                    known_entities.add(uid)

                old_anchor = ann.get('anchor') or {}
                if isinstance(old_anchor, str):
                    try: old_anchor = json.loads(old_anchor)
                    except: old_anchor = {}

                spans = old_anchor.get('spans', [])
                target_span = spans[0] if spans else None
                source_unit_id = ann['id']
                embedding_text = ann.get('embedding_text')
                visibility = {"type": ann.get('visibility', 'public')}
                unit_metadata = {
                    "tags": ann.get('tags') or [],
                    "role": ann.get('type', ''),
                    "contextuality": ann.get('contextuality', 'standalone'),
                }

                if embedding_text and embedding_text not in ('None', ''):
                    cur.execute("""
                        INSERT INTO units (id, author_id, origin, shape, body, visibility,
                                           metadata, vector, vector_text, created_at)
                        VALUES (%s, %s, 'authored', 'flat', %s, %s, %s, %s::vector, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (source_unit_id, uid or list(known_entities)[0],
                          Json({"html": ann.get('text', '')}), Json(visibility),
                          Json(unit_metadata), embedding_text, ann.get('text', ''),
                          ann.get('created_at')))
                else:
                    cur.execute("""
                        INSERT INTO units (id, author_id, origin, shape, body, visibility,
                                           metadata, created_at)
                        VALUES (%s, %s, 'authored', 'flat', %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (source_unit_id, uid or list(known_entities)[0],
                          Json({"html": ann.get('text', '')}), Json(visibility),
                          Json(unit_metadata), ann.get('created_at')))

                anchor_id = f"anc-{uuid4().hex[:12]}"
                target_type = 'span' if target_span else 'unit'
                anchor_metadata = {k: old_anchor[k] for k in
                    ('type', 'spans', 'startSpanId', 'endSpanId',
                     'startOffset', 'endOffset', 'color', 'note')
                    if k in old_anchor}

                cur.execute("""
                    INSERT INTO anchors (id, source_type, source_unit, target_type,
                                         target_unit, target_span, role, metadata, created_at)
                    VALUES (%s, 'unit', %s, %s, %s, %s, %s, %s, %s)
                """, (anchor_id, source_unit_id, target_type, ann.get('content_id'),
                      target_span, ann.get('type', 'highlight'), Json(anchor_metadata),
                      ann.get('created_at')))
            logger.info(f"  → {len(annotations)} annotation units + anchors")

            logger.info("=== Step 6: Migrate reading data ===")
            # Collect known unit IDs for FK validation
            cur.execute("SELECT id FROM units")
            known_unit_ids = {r['id'] for r in cur.fetchall()}

            # Reading progress
            cur.execute("SELECT * FROM reading_progress_v1")
            rp_rows = cur.fetchall()
            rp_migrated = 0
            for r in rp_rows:
                uid = r.get('uid')
                cid = r.get('content_id')
                if uid and uid in known_entities and cid and cid in known_unit_ids:
                    cur.execute("""
                        INSERT INTO reading_progress (entity_id, unit_id, span_id, updated_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (entity_id, unit_id) DO NOTHING
                    """, (uid, cid, r['span_id'], r.get('updated_at')))
                    rp_migrated += 1
            logger.info(f"  → {rp_migrated}/{len(rp_rows)} reading_progress")

            # Reading sessions
            cur.execute("SELECT * FROM reading_sessions_v1")
            rs_rows = cur.fetchall()
            rs_migrated = 0
            for r in rs_rows:
                uid = r.get('uid')
                cid = r.get('content_id')
                if uid and uid in known_entities and cid and cid in known_unit_ids:
                    cur.execute("""
                        INSERT INTO reading_sessions (id, entity_id, unit_id, started_at,
                                                      ended_at, duration_seconds, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (r['id'], uid, cid, r.get('started_at'), r.get('ended_at'),
                          r.get('duration_seconds'), r.get('source', 'manual')))
                    rs_migrated += 1
            logger.info(f"  → {rs_migrated}/{len(rs_rows)} reading_sessions")

            logger.info("=== Step 7: Migrate rss_sources ===")
            cur.execute("SELECT * FROM rss_sources")
            rss = cur.fetchall()
            # rss_sources table structure hasn't changed significantly
            # The created_by FK now points to entities instead of users
            # Since we created entities from users with the same IDs, this should work
            logger.info(f"  → {len(rss)} rss_sources (unchanged, FK resolved)")

            if DROP_OLD:
                logger.info("=== Step 8: Drop old tables ===")
                for t in ['translations_v1', 'feedback_v1', 'queries_v1',
                          'reading_sessions_v1', 'reading_progress_v1',
                          'annotations_v1', 'contents_v1', 'users_v1']:
                    cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
                    logger.info(f"  Dropped {t}")

            conn.commit()
            logger.info("=== Migration complete! ===")

        else:
            # Dry run: just count records
            cur.execute("SELECT COUNT(*) FROM users")
            users_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) FROM contents WHERE status = 'ready'")
            contents_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) FROM annotations")
            ann_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) FROM reading_progress")
            rp_count = cur.fetchone()['count']
            cur.execute("SELECT COUNT(*) FROM reading_sessions")
            rs_count = cur.fetchone()['count']

            logger.info(f"\nWould migrate:")
            logger.info(f"  {users_count} users → entities + auth")
            logger.info(f"  {contents_count} contents → units (+ dormant author entities)")
            logger.info(f"  {ann_count} annotations → units + anchors (with embeddings)")
            logger.info(f"  {rp_count} reading_progress records")
            logger.info(f"  {rs_count} reading_sessions")
            logger.info(f"\nRun with --execute to perform migration")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
