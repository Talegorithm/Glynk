"""
PostgresStore - PostgreSQL 存储层

6张表 + pgvector 向量搜索。单例模式。
"""
import json
import logging
from typing import Optional

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, Json
import psycopg2

from glynk.config import StorageConfig
from glynk.models import Content, Annotation

logger = logging.getLogger(__name__)

# DDL statements
INIT_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS contents (
    content_id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    author TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL,
    source_url TEXT,
    source_file_hash TEXT NOT NULL,
    file_count INT NOT NULL DEFAULT 0,
    toc_json TEXT DEFAULT '[]',
    ai_outline_json TEXT DEFAULT '[]',
    abstract TEXT DEFAULT '',
    translations JSONB DEFAULT '{}',
    uid TEXT,
    status TEXT NOT NULL DEFAULT 'parsing',
    error_message TEXT,
    total_chars INT DEFAULT 0,
    language TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contents_hash ON contents(source_file_hash);
CREATE INDEX IF NOT EXISTS idx_contents_status ON contents(status);

CREATE TABLE IF NOT EXISTS annotations (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL REFERENCES contents(content_id) ON DELETE CASCADE,
    anchor JSONB NOT NULL,
    type TEXT NOT NULL,
    text TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    contextuality TEXT DEFAULT 'standalone',
    source TEXT NOT NULL,
    uid TEXT,
    visibility TEXT NOT NULL DEFAULT 'public',
    query_id TEXT,
    embedding vector(3072),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ann_content ON annotations(content_id);
CREATE INDEX IF NOT EXISTS idx_ann_uid ON annotations(uid) WHERE uid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ann_type ON annotations(type);
CREATE INDEX IF NOT EXISTS idx_ann_visibility ON annotations(visibility);
CREATE INDEX IF NOT EXISTS idx_ann_tags ON annotations USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_ann_anchor ON annotations USING gin(anchor);

CREATE TABLE IF NOT EXISTS queries (
    query_id TEXT PRIMARY KEY,
    uid TEXT,
    user_context JSONB,
    query_text TEXT,
    result_ids TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    query_id TEXT REFERENCES queries(query_id),
    result_id TEXT NOT NULL,
    presented BOOLEAN DEFAULT false,
    clicked_through BOOLEAN DEFAULT false,
    agent_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rss_sources (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    name TEXT DEFAULT '',
    content_type TEXT,
    schedule TEXT DEFAULT 'daily',
    max_items INT DEFAULT 5,
    enabled BOOLEAN DEFAULT true,
    filters JSONB DEFAULT '{}',
    created_by TEXT,
    last_fetched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    name TEXT DEFAULT '',
    preferred_lang TEXT DEFAULT 'zh',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reading_progress (
    uid TEXT NOT NULL,
    content_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid, content_id)
);

CREATE TABLE IF NOT EXISTS reading_sessions (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    content_id TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    source TEXT DEFAULT 'manual'
);

CREATE INDEX IF NOT EXISTS idx_rs_uid ON reading_sessions(uid);
CREATE INDEX IF NOT EXISTS idx_rs_content ON reading_sessions(content_id);

CREATE TABLE IF NOT EXISTS translations (
    content_id TEXT NOT NULL REFERENCES contents(content_id) ON DELETE CASCADE,
    file_idx INT NOT NULL,
    language TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    progress FLOAT DEFAULT 0,
    total_paragraphs INT DEFAULT 0,
    translated_paragraphs INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    PRIMARY KEY (content_id, file_idx, language)
);
"""

# Vector index: pgvector IVFFlat/HNSW both cap at 2000 dims, 3072 dims uses brute-force scan.
# At 110K rows this is fine (~50ms). For 1M+ rows, consider dimensionality reduction or Milvus.
VECTOR_INDEX_SQL = ""


class PostgresStore:
    """PostgreSQL 存储层。单例。"""

    _instance = None

    @classmethod
    def get_instance(cls, config: StorageConfig = None) -> 'PostgresStore':
        if cls._instance is None:
            if config is None:
                raise ValueError("StorageConfig required for first initialization")
            cls._instance = cls(config)
        return cls._instance

    def __init__(self, config: StorageConfig):
        self.pool = ThreadedConnectionPool(
            1, 10,
            host=config.postgres_host,
            port=config.postgres_port,
            user=config.postgres_user,
            password=config.postgres_password,
            dbname=config.postgres_db,
        )
        self._init_tables()

    def _init_tables(self):
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(INIT_SQL)
            conn.commit()
            logger.info("Database tables initialized")
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize tables: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def _execute(self, sql: str, params=None, fetch: str = None):
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                if fetch == 'one':
                    result = cur.fetchone()
                elif fetch == 'all':
                    result = cur.fetchall()
                else:
                    result = None
            conn.commit()
            return dict(result) if result and fetch == 'one' else (
                [dict(r) for r in result] if result and fetch == 'all' else None
            )
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    # --- Contents ---

    def create_content(self, content: Content) -> bool:
        sql = """
            INSERT INTO contents (content_id, title, author, source_type, source_url,
                source_file_hash, file_count, toc_json, ai_outline_json, abstract,
                translations, uid, status, total_chars)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (content_id) DO NOTHING
        """
        self._execute(sql, (
            content.content_id, content.title, content.author, content.source_type,
            content.source_url, content.source_file_hash, content.file_count,
            content.toc_json, content.ai_outline_json, content.abstract,
            Json(content.translations), content.uid, content.status, content.total_chars,
        ))
        return True

    def delete_content(self, content_id: str) -> bool:
        """删除内容及关联数据（annotations 通过 ON DELETE CASCADE 自动删除）"""
        self._execute("DELETE FROM contents WHERE content_id = %s", (content_id,))
        return True

    def get_content(self, content_id: str) -> Optional[dict]:
        return self._execute(
            "SELECT * FROM contents WHERE content_id = %s",
            (content_id,), fetch='one'
        )

    def get_content_by_source_url(self, normalized_url: str) -> Optional[dict]:
        """按归一化 URL 前缀匹配查找内容（去掉 tracking 参数后的 URL）"""
        return self._execute(
            "SELECT * FROM contents WHERE source_url LIKE %s AND status = 'ready' LIMIT 1",
            (normalized_url + '%',), fetch='one'
        )

    def list_contents(self, limit: int = 100, offset: int = 0) -> list[dict]:
        return self._execute(
            "SELECT * FROM contents WHERE status = 'ready' ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset), fetch='all'
        ) or []

    def count_contents(self) -> int:
        result = self._execute("SELECT count(*) FROM contents WHERE status = 'ready'", fetch='one')
        return result['count'] if result else 0

    def update_content_outline(self, content_id: str, outline_json: str) -> bool:
        self._execute(
            "UPDATE contents SET ai_outline_json = %s, updated_at = CURRENT_TIMESTAMP WHERE content_id = %s",
            (outline_json, content_id),
        )
        return True

    # --- Annotations ---

    def create_annotation(self, ann: Annotation, embedding: list[float] = None) -> bool:
        embedding_str = str(embedding) if embedding else None
        sql = """
            INSERT INTO annotations (id, content_id, anchor, type, text, tags,
                contextuality, source, uid, visibility, query_id, embedding, version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._execute(sql, (
            ann.id, ann.content_id, Json(ann.anchor), ann.type, ann.text,
            ann.tags, ann.contextuality, ann.source, ann.uid, ann.visibility,
            ann.query_id, embedding_str, ann.version,
        ))
        return True

    def create_annotations_batch(self, anns: list[Annotation], embeddings: list = None) -> int:
        if not anns:
            return 0

        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                for i, ann in enumerate(anns):
                    emb = embeddings[i] if embeddings and embeddings[i] else None
                    emb_str = str(emb) if emb else None
                    cur.execute("""
                        INSERT INTO annotations (id, content_id, anchor, type, text, tags,
                            contextuality, source, uid, visibility, query_id, embedding, version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        ann.id, ann.content_id, Json(ann.anchor), ann.type, ann.text,
                        ann.tags, ann.contextuality, ann.source, ann.uid, ann.visibility,
                        ann.query_id, emb_str, ann.version,
                    ))
            conn.commit()
            return len(anns)
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def get_annotations(self, content_id: str, uid: str = None) -> list[dict]:
        if uid:
            sql = """
                SELECT id, content_id, anchor, type, text, tags, contextuality,
                       source, visibility, created_at
                FROM annotations
                WHERE content_id = %s AND (visibility = 'public' OR uid = %s)
                ORDER BY created_at
            """
            return self._execute(sql, (content_id, uid), fetch='all') or []
        else:
            sql = """
                SELECT id, content_id, anchor, type, text, tags, contextuality,
                       source, visibility, created_at
                FROM annotations
                WHERE content_id = %s AND visibility = 'public'
                ORDER BY created_at
            """
            return self._execute(sql, (content_id,), fetch='all') or []

    def get_user_annotations(self, uid: str, content_id: str = None,
                             type: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        conditions = ["uid = %s"]
        params = [uid]

        if content_id:
            conditions.append("content_id = %s")
            params.append(content_id)
        if type:
            conditions.append("type = %s")
            params.append(type)

        where = " AND ".join(conditions)
        params.extend([limit, offset])

        sql = f"""
            SELECT id, content_id, anchor, type, text, tags, contextuality,
                   source, visibility, created_at
            FROM annotations
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return self._execute(sql, tuple(params), fetch='all') or []

    def count_user_annotations(self, uid: str, content_id: str = None, type: str = None) -> int:
        conditions = ["uid = %s"]
        params = [uid]
        if content_id:
            conditions.append("content_id = %s")
            params.append(content_id)
        if type:
            conditions.append("type = %s")
            params.append(type)

        where = " AND ".join(conditions)
        result = self._execute(
            f"SELECT COUNT(*) as count FROM annotations WHERE {where}",
            tuple(params), fetch='one'
        )
        return result['count'] if result else 0

    def delete_annotation(self, ann_id: str, uid: str) -> bool:
        result = self._execute(
            "DELETE FROM annotations WHERE id = %s AND uid = %s RETURNING id",
            (ann_id, uid), fetch='one'
        )
        return result is not None

    def update_annotation(self, ann_id: str, uid: str, **kwargs) -> Optional[dict]:
        sets = []
        params = []
        for k, v in kwargs.items():
            if k == 'anchor':
                sets.append(f"{k} = %s")
                params.append(Json(v))
            else:
                sets.append(f"{k} = %s")
                params.append(v)
        if not sets:
            return None
        params.extend([ann_id, uid])
        sql = f"""
            UPDATE annotations SET {', '.join(sets)}
            WHERE id = %s AND uid = %s
            RETURNING id, content_id, anchor, type, text, tags, contextuality,
                      source, visibility, created_at
        """
        return self._execute(sql, tuple(params), fetch='one')

    def get_span_crowd_count(self, span_id: str) -> int:
        sql = """
            SELECT COUNT(DISTINCT uid) as count FROM annotations
            WHERE anchor->'spans' ? %s AND visibility = 'public'
        """
        result = self._execute(sql, (span_id,), fetch='one')
        return result['count'] if result else 0

    # --- Queries ---

    def create_query(self, query_id, uid, user_context, text, result_ids) -> bool:
        sql = """
            INSERT INTO queries (query_id, uid, user_context, query_text, result_ids)
            VALUES (%s, %s, %s, %s, %s)
        """
        self._execute(sql, (query_id, uid, Json(user_context), text, result_ids))
        return True

    # --- Feedback ---

    def create_feedback(self, feedback_id, query_id, result_id,
                        presented=False, clicked_through=False, agent_summary=None) -> bool:
        sql = """
            INSERT INTO feedback (id, query_id, result_id, presented, clicked_through, agent_summary)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        self._execute(sql, (feedback_id, query_id, result_id, presented, clicked_through, agent_summary))
        return True

    # --- RSS Sources ---

    def create_source(self, source_id, url, name="", content_type=None,
                      schedule="daily", max_items=5, filters=None, created_by=None) -> bool:
        sql = """
            INSERT INTO rss_sources (id, url, name, content_type, schedule, max_items, filters, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self._execute(sql, (source_id, url, name, content_type, schedule, max_items,
                            Json(filters or {}), created_by))
        return True

    def list_sources(self, enabled_only: bool = True) -> list[dict]:
        if enabled_only:
            return self._execute(
                "SELECT * FROM rss_sources WHERE enabled = true ORDER BY created_at",
                fetch='all'
            ) or []
        return self._execute("SELECT * FROM rss_sources ORDER BY created_at", fetch='all') or []

    def get_source(self, source_id: str) -> Optional[dict]:
        return self._execute("SELECT * FROM rss_sources WHERE id = %s", (source_id,), fetch='one')

    def update_source(self, source_id: str, **kwargs) -> bool:
        sets = []
        params = []
        for k, v in kwargs.items():
            if k == 'filters':
                sets.append(f"{k} = %s")
                params.append(Json(v))
            else:
                sets.append(f"{k} = %s")
                params.append(v)
        params.append(source_id)
        sql = f"UPDATE rss_sources SET {', '.join(sets)} WHERE id = %s"
        self._execute(sql, tuple(params))
        return True

    def update_source_last_fetched(self, source_id: str) -> bool:
        self._execute(
            "UPDATE rss_sources SET last_fetched_at = CURRENT_TIMESTAMP WHERE id = %s",
            (source_id,)
        )
        return True

    def delete_source(self, source_id: str) -> bool:
        self._execute("DELETE FROM rss_sources WHERE id = %s", (source_id,))
        return True

    # --- Users ---

    def create_user(self, uid: str, token: str, email: str, name: str = "") -> bool:
        sql = """
            INSERT INTO users (uid, token, email, name)
            VALUES (%s, %s, %s, %s)
        """
        self._execute(sql, (uid, token, email, name))
        return True

    def get_user_by_token(self, token: str) -> Optional[dict]:
        return self._execute("SELECT * FROM users WHERE token = %s", (token,), fetch='one')

    def get_user_by_uid(self, uid: str) -> Optional[dict]:
        return self._execute("SELECT * FROM users WHERE uid = %s", (uid,), fetch='one')

    def get_user_by_email(self, email: str) -> Optional[dict]:
        return self._execute("SELECT * FROM users WHERE email = %s", (email,), fetch='one')

    # --- Reading Progress ---

    def upsert_reading_progress(self, uid: str, content_id: str, span_id: str) -> bool:
        sql = """
            INSERT INTO reading_progress (uid, content_id, span_id, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (uid, content_id) DO UPDATE SET
                span_id = EXCLUDED.span_id,
                updated_at = CURRENT_TIMESTAMP
        """
        self._execute(sql, (uid, content_id, span_id))
        return True

    def get_reading_progress(self, uid: str, content_id: str) -> Optional[dict]:
        return self._execute(
            "SELECT span_id, updated_at FROM reading_progress WHERE uid = %s AND content_id = %s",
            (uid, content_id), fetch='one'
        )

    # --- Reading Sessions ---

    def create_reading_session(self, session_id: str, uid: str,
                               content_id: str, source: str = 'manual') -> bool:
        sql = """
            INSERT INTO reading_sessions (id, uid, content_id, source)
            VALUES (%s, %s, %s, %s)
        """
        self._execute(sql, (session_id, uid, content_id, source))
        return True

    def end_reading_session(self, session_id: str, duration_seconds: int = None) -> bool:
        sql = """
            UPDATE reading_sessions
            SET ended_at = CURRENT_TIMESTAMP, duration_seconds = %s
            WHERE id = %s
        """
        self._execute(sql, (duration_seconds, session_id))
        return True

    # --- Vector search ---

    def execute_query(self, sql: str, params: tuple) -> list[dict]:
        return self._execute(sql, params, fetch='all') or []
