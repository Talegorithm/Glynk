"""
PostgresStore - PostgreSQL 存储层

核心 3 表 (entities, units, anchors) + sidecar 表。
"""
import json
import logging
from typing import Optional

from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor, Json
import psycopg2

from glynk.config import StorageConfig

logger = logging.getLogger(__name__)

INIT_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

-- Core: Entity
CREATE TABLE IF NOT EXISTS entities (
    id            TEXT PRIMARY KEY,
    kind          TEXT NOT NULL DEFAULT 'human',
    state         TEXT NOT NULL DEFAULT 'active',
    display_name  TEXT NOT NULL DEFAULT '',
    bio           TEXT DEFAULT '',
    agent_uri     TEXT,
    inspired_by   TEXT REFERENCES entities(id),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Core: Unit
CREATE TABLE IF NOT EXISTS units (
    id            TEXT PRIMARY KEY,
    author_id     TEXT NOT NULL REFERENCES entities(id),
    origin        TEXT NOT NULL,
    shape         TEXT NOT NULL DEFAULT 'flat',
    body          JSONB NOT NULL DEFAULT '{}',
    visibility    JSONB DEFAULT '{"type":"public"}',
    metadata      JSONB DEFAULT '{}',
    vector        vector(3072),
    vector_text   TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_units_author ON units(author_id);
CREATE INDEX IF NOT EXISTS idx_units_origin ON units(origin);
CREATE INDEX IF NOT EXISTS idx_units_metadata ON units USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_units_content_hash ON units((metadata->>'content_hash'));

-- Core: Anchor
CREATE TABLE IF NOT EXISTS anchors (
    id              TEXT PRIMARY KEY,
    source_type     TEXT NOT NULL,
    source_unit     TEXT REFERENCES units(id) ON DELETE CASCADE,
    source_entity   TEXT REFERENCES entities(id),
    target_type     TEXT NOT NULL,
    target_unit     TEXT REFERENCES units(id),
    target_span     TEXT,
    target_entity   TEXT REFERENCES entities(id),
    role            TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchors_source_unit ON anchors(source_unit);
CREATE INDEX IF NOT EXISTS idx_anchors_target_unit ON anchors(target_unit);
CREATE INDEX IF NOT EXISTS idx_anchors_target_span ON anchors(target_span);
CREATE INDEX IF NOT EXISTS idx_anchors_source_entity ON anchors(source_entity);
CREATE INDEX IF NOT EXISTS idx_anchors_target_entity ON anchors(target_entity);
CREATE INDEX IF NOT EXISTS idx_anchors_role ON anchors(role);

-- Auth
CREATE TABLE IF NOT EXISTS auth (
    entity_id   TEXT PRIMARY KEY REFERENCES entities(id),
    token       TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- User state
CREATE TABLE IF NOT EXISTS reading_progress (
    entity_id   TEXT NOT NULL REFERENCES entities(id),
    unit_id     TEXT NOT NULL REFERENCES units(id),
    span_id     TEXT NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (entity_id, unit_id)
);

CREATE TABLE IF NOT EXISTS reading_sessions (
    id              TEXT PRIMARY KEY,
    entity_id       TEXT NOT NULL REFERENCES entities(id),
    unit_id         TEXT NOT NULL REFERENCES units(id),
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    duration_seconds INTEGER,
    source          TEXT DEFAULT 'manual'
);

-- Event log
CREATE TABLE IF NOT EXISTS event_log (
    id            TEXT PRIMARY KEY,
    actor_id      TEXT NOT NULL REFERENCES entities(id),
    event_type    TEXT NOT NULL,
    subject_unit  TEXT REFERENCES units(id),
    subject_span  TEXT,
    payload       JSONB DEFAULT '{}',
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_actor ON event_log(actor_id);
CREATE INDEX IF NOT EXISTS idx_event_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_unit ON event_log(subject_unit);

-- Config
CREATE TABLE IF NOT EXISTS rss_sources (
    id            TEXT PRIMARY KEY,
    url           TEXT NOT NULL,
    name          TEXT DEFAULT '',
    content_type  TEXT,
    schedule      TEXT DEFAULT 'daily',
    max_items     INT DEFAULT 5,
    enabled       BOOLEAN DEFAULT true,
    filters       JSONB DEFAULT '{}',
    created_by    TEXT REFERENCES entities(id),
    last_fetched_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
"""


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

    # --- Entities ---

    def create_entity(self, entity_id: str, kind: str = 'human', state: str = 'active',
                      display_name: str = '', bio: str = '', agent_uri: str = None,
                      inspired_by: str = None) -> bool:
        sql = """
            INSERT INTO entities (id, kind, state, display_name, bio, agent_uri, inspired_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """
        self._execute(sql, (entity_id, kind, state, display_name, bio, agent_uri, inspired_by))
        return True

    def get_entity(self, entity_id: str) -> Optional[dict]:
        return self._execute("SELECT * FROM entities WHERE id = %s", (entity_id,), fetch='one')

    def find_entity_by_name(self, display_name: str, state: str = None) -> Optional[dict]:
        if state:
            return self._execute(
                "SELECT * FROM entities WHERE display_name = %s AND state = %s LIMIT 1",
                (display_name, state), fetch='one'
            )
        return self._execute(
            "SELECT * FROM entities WHERE display_name = %s LIMIT 1",
            (display_name,), fetch='one'
        )

    def update_entity(self, entity_id: str, **kwargs) -> bool:
        if not kwargs:
            return True
        sets, params = [], []
        for k, v in kwargs.items():
            sets.append(f"{k} = %s")
            params.append(v)
        params.append(entity_id)
        self._execute(f"UPDATE entities SET {', '.join(sets)} WHERE id = %s", tuple(params))
        return True

    # --- Auth ---

    def create_auth(self, entity_id: str, token: str, email: str) -> bool:
        self._execute(
            "INSERT INTO auth (entity_id, token, email) VALUES (%s, %s, %s)",
            (entity_id, token, email),
        )
        return True

    def get_auth_by_token(self, token: str) -> Optional[dict]:
        return self._execute(
            """SELECT a.*, e.display_name, e.kind, e.state
               FROM auth a JOIN entities e ON a.entity_id = e.id
               WHERE a.token = %s""",
            (token,), fetch='one',
        )

    def get_auth_by_email(self, email: str) -> Optional[dict]:
        return self._execute(
            """SELECT a.*, e.display_name
               FROM auth a JOIN entities e ON a.entity_id = e.id
               WHERE a.email = %s""",
            (email,), fetch='one',
        )

    def get_auth_by_entity(self, entity_id: str) -> Optional[dict]:
        return self._execute(
            """SELECT a.*, e.display_name, e.kind, e.state
               FROM auth a JOIN entities e ON a.entity_id = e.id
               WHERE a.entity_id = %s""",
            (entity_id,), fetch='one',
        )

    # --- Units ---

    def create_unit(self, unit_id: str, author_id: str, origin: str, shape: str = 'flat',
                    body: dict = None, visibility: dict = None, metadata: dict = None,
                    vector: list = None, vector_text: str = None) -> bool:
        embedding_str = str(vector) if vector else None
        sql = """
            INSERT INTO units (id, author_id, origin, shape, body, visibility, metadata, vector, vector_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """
        self._execute(sql, (
            unit_id, author_id, origin, shape,
            Json(body or {}), Json(visibility or {"type": "public"}),
            Json(metadata or {}), embedding_str, vector_text,
        ))
        return True

    def create_unit_with_vector(self, unit_id: str, author_id: str, origin: str,
                                shape: str = 'flat', body: dict = None,
                                visibility: dict = None, metadata: dict = None,
                                vector: list = None, vector_text: str = None) -> bool:
        """Create unit, used by batch operations that pre-compute vectors."""
        return self.create_unit(unit_id, author_id, origin, shape, body,
                                visibility, metadata, vector, vector_text)

    def create_units_batch(self, units: list[dict], vectors: list = None) -> int:
        """Batch insert units with optional vectors."""
        if not units:
            return 0
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                for i, u in enumerate(units):
                    vec = vectors[i] if vectors and i < len(vectors) and vectors[i] else None
                    vec_str = str(vec) if vec else None
                    cur.execute("""
                        INSERT INTO units (id, author_id, origin, shape, body, visibility,
                                           metadata, vector, vector_text)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        u['id'], u['author_id'], u['origin'], u.get('shape', 'flat'),
                        Json(u.get('body', {})), Json(u.get('visibility', {"type": "public"})),
                        Json(u.get('metadata', {})), vec_str, u.get('vector_text'),
                    ))
            conn.commit()
            return len(units)
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def delete_unit(self, unit_id: str) -> bool:
        """
        事务级联删除一个 Unit 及其所有依赖。

        schema 里只有 anchors.source_unit 是 ON DELETE CASCADE；
        别的外键（anchors.target_unit, reading_progress/sessions, event_log.subject_unit）
        会阻断 DELETE，所以要手动清理：

        1. 清 reading state（progress / sessions）
        2. 清 event_log 里指向它的记录
        3. 删所有"标注这个 Unit"的 authored source Unit（从而级联删这些 anchor）
        4. 删剩下仅剩 source=entity 的 anchor（like / bookmark 等，没 source_unit）
        5. 删 Unit 本体（级联它作为 source_unit 的 anchors）

        注意 step 3：标注（别人写的 note / highlight / hook）会随之消失 —— 它们
        离开 target 就失去语义。早期产品阶段接受这个行为，以后可考虑"悬空标记"保留。
        """
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM reading_sessions WHERE unit_id = %s", (unit_id,))
                cur.execute("DELETE FROM reading_progress WHERE unit_id = %s", (unit_id,))
                cur.execute("DELETE FROM event_log WHERE subject_unit = %s", (unit_id,))
                cur.execute(
                    """DELETE FROM units WHERE id IN (
                           SELECT source_unit FROM anchors
                           WHERE target_unit = %s AND source_unit IS NOT NULL
                       )""",
                    (unit_id,),
                )
                cur.execute("DELETE FROM anchors WHERE target_unit = %s", (unit_id,))
                cur.execute("DELETE FROM units WHERE id = %s", (unit_id,))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def get_unit(self, unit_id: str) -> Optional[dict]:
        return self._execute(
            """SELECT u.*, e.display_name as author_name
               FROM units u JOIN entities e ON u.author_id = e.id
               WHERE u.id = %s""",
            (unit_id,), fetch='one',
        )

    def get_unit_by_content_hash(self, content_hash: str) -> Optional[dict]:
        """按内容 hash 查找 Unit。用于摄入去重（同内容幂等）。"""
        return self._execute(
            """SELECT u.*, e.display_name as author_name
               FROM units u JOIN entities e ON u.author_id = e.id
               WHERE u.metadata->>'content_hash' = %s
                 AND u.metadata->>'status' = 'ready'
               LIMIT 1""",
            (content_hash,), fetch='one',
        )

    def list_units(self, origin: str = None, limit: int = 100, offset: int = 0,
                   author_id: str = None) -> list[dict]:
        conditions = ["metadata->>'status' IS DISTINCT FROM 'error'"]
        params = []
        if origin:
            conditions.append("u.origin = %s")
            params.append(origin)
        if author_id:
            conditions.append("u.author_id = %s")
            params.append(author_id)
        where = "WHERE " + " AND ".join(conditions)
        params.extend([limit, offset])
        return self._execute(f"""
            SELECT u.*, e.display_name as author_name
            FROM units u JOIN entities e ON u.author_id = e.id
            {where}
            ORDER BY u.created_at DESC LIMIT %s OFFSET %s
        """, tuple(params), fetch='all') or []

    def count_units(self, origin: str = None, author_id: str = None) -> int:
        conditions = ["metadata->>'status' IS DISTINCT FROM 'error'"]
        params = []
        if origin:
            conditions.append("origin = %s")
            params.append(origin)
        if author_id:
            conditions.append("author_id = %s")
            params.append(author_id)
        where = "WHERE " + " AND ".join(conditions)
        result = self._execute(
            f"SELECT COUNT(*) as count FROM units {where}", tuple(params), fetch='one',
        )
        return result['count'] if result else 0

    def update_unit(self, unit_id: str, **kwargs) -> bool:
        if not kwargs:
            return True
        sets, params = [], []
        for k, v in kwargs.items():
            if k in ('body', 'visibility', 'metadata'):
                sets.append(f"{k} = %s")
                params.append(Json(v))
            elif k == 'vector':
                sets.append(f"{k} = %s")
                params.append(str(v) if v else None)
            else:
                sets.append(f"{k} = %s")
                params.append(v)
        params.append(unit_id)
        self._execute(f"UPDATE units SET {', '.join(sets)} WHERE id = %s", tuple(params))
        return True

    def update_unit_metadata_key(self, unit_id: str, key: str, value) -> bool:
        self._execute(
            "UPDATE units SET metadata = jsonb_set(COALESCE(metadata, '{}'), %s, %s) WHERE id = %s",
            (f'{{{key}}}', Json(value), unit_id),
        )
        return True

    # --- Anchors ---

    def create_anchor(self, anchor_id: str, source_type: str, target_type: str,
                      role: str, source_unit: str = None, source_entity: str = None,
                      target_unit: str = None, target_span: str = None,
                      target_entity: str = None, metadata: dict = None) -> bool:
        self._execute("""
            INSERT INTO anchors (id, source_type, source_unit, source_entity,
                target_type, target_unit, target_span, target_entity, role, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            anchor_id, source_type, source_unit, source_entity,
            target_type, target_unit, target_span, target_entity,
            role, Json(metadata or {}),
        ))
        return True

    def create_anchors_batch(self, anchors: list[dict]) -> int:
        if not anchors:
            return 0
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                for a in anchors:
                    cur.execute("""
                        INSERT INTO anchors (id, source_type, source_unit, source_entity,
                            target_type, target_unit, target_span, target_entity, role, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        a['id'], a['source_type'], a.get('source_unit'), a.get('source_entity'),
                        a['target_type'], a.get('target_unit'), a.get('target_span'),
                        a.get('target_entity'), a['role'], Json(a.get('metadata', {})),
                    ))
            conn.commit()
            return len(anchors)
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def get_anchors_for_unit(self, target_unit: str, entity_id: str = None) -> list[dict]:
        """Get all anchors targeting a unit, with source unit body/metadata."""
        if entity_id:
            return self._execute("""
                SELECT a.id, a.source_type, a.source_unit, a.source_entity,
                       a.target_type, a.target_unit, a.target_span, a.role,
                       a.metadata, a.created_at,
                       su.body as source_body, su.metadata as source_metadata,
                       su.author_id, su.visibility as source_visibility,
                       e.display_name as author_name
                FROM anchors a
                LEFT JOIN units su ON a.source_unit = su.id
                LEFT JOIN entities e ON COALESCE(su.author_id, a.source_entity) = e.id
                WHERE a.target_unit = %s
                  AND (su.visibility->>'type' = 'public'
                       OR su.author_id = %s
                       OR a.source_entity = %s
                       OR a.source_unit IS NULL)
                ORDER BY a.created_at
            """, (target_unit, entity_id, entity_id), fetch='all') or []
        else:
            return self._execute("""
                SELECT a.id, a.source_type, a.source_unit, a.source_entity,
                       a.target_type, a.target_unit, a.target_span, a.role,
                       a.metadata, a.created_at,
                       su.body as source_body, su.metadata as source_metadata,
                       su.author_id, su.visibility as source_visibility,
                       e.display_name as author_name
                FROM anchors a
                LEFT JOIN units su ON a.source_unit = su.id
                LEFT JOIN entities e ON COALESCE(su.author_id, a.source_entity) = e.id
                WHERE a.target_unit = %s
                  AND (su.visibility->>'type' = 'public'
                       OR a.source_unit IS NULL)
                ORDER BY a.created_at
            """, (target_unit,), fetch='all') or []

    def get_anchors_by_entity(self, entity_id: str, target_unit: str = None,
                              role: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        conditions = ["(su.author_id = %s OR a.source_entity = %s)"]
        params = [entity_id, entity_id]
        if target_unit:
            conditions.append("a.target_unit = %s")
            params.append(target_unit)
        if role:
            conditions.append("a.role = %s")
            params.append(role)
        where = " AND ".join(conditions)
        params.extend([limit, offset])
        return self._execute(f"""
            SELECT a.*, su.body as source_body, su.metadata as source_metadata,
                   tu.metadata as target_metadata
            FROM anchors a
            LEFT JOIN units su ON a.source_unit = su.id
            LEFT JOIN units tu ON a.target_unit = tu.id
            WHERE {where}
            ORDER BY a.created_at DESC LIMIT %s OFFSET %s
        """, tuple(params), fetch='all') or []

    def count_anchors_by_entity(self, entity_id: str, target_unit: str = None,
                                role: str = None) -> int:
        conditions = [
            "(EXISTS (SELECT 1 FROM units u2 WHERE u2.id = a.source_unit AND u2.author_id = %s)"
            " OR a.source_entity = %s)"
        ]
        params = [entity_id, entity_id]
        if target_unit:
            conditions.append("a.target_unit = %s")
            params.append(target_unit)
        if role:
            conditions.append("a.role = %s")
            params.append(role)
        where = " AND ".join(conditions)
        result = self._execute(
            f"SELECT COUNT(*) as count FROM anchors a WHERE {where}",
            tuple(params), fetch='one',
        )
        return result['count'] if result else 0

    def delete_anchor(self, anchor_id: str, entity_id: str) -> bool:
        result = self._execute("""
            DELETE FROM anchors WHERE id = %s AND (
                source_entity = %s
                OR source_unit IN (SELECT id FROM units WHERE author_id = %s)
            ) RETURNING id
        """, (anchor_id, entity_id, entity_id), fetch='one')
        return result is not None

    def update_anchor(self, anchor_id: str, entity_id: str, **kwargs) -> Optional[dict]:
        sets, params = [], []
        for k, v in kwargs.items():
            if k == 'metadata':
                sets.append(f"{k} = %s")
                params.append(Json(v))
            else:
                sets.append(f"{k} = %s")
                params.append(v)
        if not sets:
            return None
        params.extend([anchor_id, entity_id, entity_id])
        return self._execute(f"""
            UPDATE anchors SET {', '.join(sets)}
            WHERE id = %s AND (
                source_entity = %s
                OR source_unit IN (SELECT id FROM units WHERE author_id = %s)
            ) RETURNING *
        """, tuple(params), fetch='one')

    def get_span_crowd_count(self, span_id: str) -> int:
        result = self._execute("""
            SELECT COUNT(DISTINCT COALESCE(a.source_entity, su.author_id)) as count
            FROM anchors a
            LEFT JOIN units su ON a.source_unit = su.id
            WHERE a.target_span = %s
        """, (span_id,), fetch='one')
        return result['count'] if result else 0

    # --- Event Log ---

    def log_event(self, event_id: str, actor_id: str, event_type: str,
                  subject_unit: str = None, subject_span: str = None,
                  payload: dict = None) -> bool:
        self._execute("""
            INSERT INTO event_log (id, actor_id, event_type, subject_unit, subject_span, payload)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (event_id, actor_id, event_type, subject_unit, subject_span, Json(payload or {})))
        return True

    # --- Reading Progress ---

    def upsert_reading_progress(self, entity_id: str, unit_id: str, span_id: str) -> bool:
        self._execute("""
            INSERT INTO reading_progress (entity_id, unit_id, span_id, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (entity_id, unit_id) DO UPDATE SET
                span_id = EXCLUDED.span_id, updated_at = NOW()
        """, (entity_id, unit_id, span_id))
        return True

    def get_reading_progress(self, entity_id: str, unit_id: str) -> Optional[dict]:
        return self._execute(
            "SELECT span_id, updated_at FROM reading_progress WHERE entity_id = %s AND unit_id = %s",
            (entity_id, unit_id), fetch='one',
        )

    # --- Reading Sessions ---

    def create_reading_session(self, session_id: str, entity_id: str,
                               unit_id: str, source: str = 'manual') -> bool:
        self._execute(
            "INSERT INTO reading_sessions (id, entity_id, unit_id, source) VALUES (%s, %s, %s, %s)",
            (session_id, entity_id, unit_id, source),
        )
        return True

    def end_reading_session(self, session_id: str, duration_seconds: int = None) -> bool:
        self._execute(
            "UPDATE reading_sessions SET ended_at = NOW(), duration_seconds = %s WHERE id = %s",
            (duration_seconds, session_id),
        )
        return True

    # --- RSS Sources ---

    def create_source(self, source_id, url, name="", content_type=None,
                      schedule="daily", max_items=5, filters=None, created_by=None) -> bool:
        self._execute("""
            INSERT INTO rss_sources (id, url, name, content_type, schedule, max_items, filters, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (source_id, url, name, content_type, schedule, max_items,
              Json(filters or {}), created_by))
        return True

    def list_sources(self, enabled_only: bool = True) -> list[dict]:
        if enabled_only:
            return self._execute(
                "SELECT * FROM rss_sources WHERE enabled = true ORDER BY created_at",
                fetch='all',
            ) or []
        return self._execute("SELECT * FROM rss_sources ORDER BY created_at", fetch='all') or []

    def get_source(self, source_id: str) -> Optional[dict]:
        return self._execute("SELECT * FROM rss_sources WHERE id = %s", (source_id,), fetch='one')

    def update_source(self, source_id: str, **kwargs) -> bool:
        sets, params = [], []
        for k, v in kwargs.items():
            sets.append(f"{k} = %s")
            params.append(Json(v) if k == 'filters' else v)
        params.append(source_id)
        self._execute(f"UPDATE rss_sources SET {', '.join(sets)} WHERE id = %s", tuple(params))
        return True

    def update_source_last_fetched(self, source_id: str) -> bool:
        self._execute("UPDATE rss_sources SET last_fetched_at = NOW() WHERE id = %s", (source_id,))
        return True

    def delete_source(self, source_id: str) -> bool:
        self._execute("DELETE FROM rss_sources WHERE id = %s", (source_id,))
        return True

    # --- Vector search (raw SQL) ---

    def execute_query(self, sql: str, params: tuple) -> list[dict]:
        return self._execute(sql, params, fetch='all') or []
