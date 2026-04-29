import uuid
from typing import Optional, List, Dict
from datetime import datetime
from glynk.storage.postgres import PostgresStore

INIT_TIMETRACK_SQL = """
CREATE TABLE IF NOT EXISTS tt_tags (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(id),
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tt_sessions (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(id),
    tag_id TEXT NOT NULL REFERENCES tt_tags(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tt_tags_entity ON tt_tags(entity_id);
CREATE INDEX IF NOT EXISTS idx_tt_sessions_entity ON tt_sessions(entity_id);
CREATE INDEX IF NOT EXISTS idx_tt_sessions_tag ON tt_sessions(tag_id);
"""

def init_timetrack_tables():
    db = PostgresStore.get_instance()
    conn = db.pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(INIT_TIMETRACK_SQL)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        db.pool.putconn(conn)

class TimetrackStore:
    def __init__(self):
        self.db = PostgresStore.get_instance()

    # --- Tags ---

    def create_tag(self, entity_id: str, name: str, color: str) -> dict:
        tag_id = uuid.uuid4().hex[:16]
        # Get max sort_order
        result = self.db._execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order FROM tt_tags WHERE entity_id = %s",
            (entity_id,), fetch='one'
        )
        sort_order = result['next_order'] if result else 0

        self.db._execute(
            """INSERT INTO tt_tags (id, entity_id, name, color, sort_order) 
               VALUES (%s, %s, %s, %s, %s)""",
            (tag_id, entity_id, name, color, sort_order)
        )
        return self.get_tag(tag_id)

    def get_tag(self, tag_id: str) -> Optional[dict]:
        return self.db._execute("SELECT * FROM tt_tags WHERE id = %s", (tag_id,), fetch='one')

    def list_tags(self, entity_id: str) -> List[dict]:
        return self.db._execute(
            "SELECT * FROM tt_tags WHERE entity_id = %s ORDER BY sort_order ASC",
            (entity_id,), fetch='all'
        ) or []

    def update_tag(self, tag_id: str, entity_id: str, **kwargs) -> Optional[dict]:
        if not kwargs:
            return self.get_tag(tag_id)
        sets, params = [], []
        for k, v in kwargs.items():
            sets.append(f"{k} = %s")
            params.append(v)
        params.extend([tag_id, entity_id])
        self.db._execute(
            f"UPDATE tt_tags SET {', '.join(sets)} WHERE id = %s AND entity_id = %s",
            tuple(params)
        )
        return self.get_tag(tag_id)

    def delete_tag(self, tag_id: str, entity_id: str) -> bool:
        self.db._execute(
            "DELETE FROM tt_tags WHERE id = %s AND entity_id = %s",
            (tag_id, entity_id)
        )
        return True

    def reorder_tags(self, entity_id: str, items: List[Dict[str, int]]):
        conn = self.db.pool.getconn()
        try:
            with conn.cursor() as cur:
                for item in items:
                    cur.execute(
                        "UPDATE tt_tags SET sort_order = %s WHERE id = %s AND entity_id = %s",
                        (item['sort_order'], item['id'], entity_id)
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.db.pool.putconn(conn)

    # --- Sessions ---

    def start_session(self, entity_id: str, tag_id: str, single_mode: bool = False) -> dict:
        if single_mode:
            # Stop all other active sessions for this user
            self.db._execute(
                "UPDATE tt_sessions SET end_time = NOW() WHERE entity_id = %s AND end_time IS NULL",
                (entity_id,)
            )
        
        session_id = uuid.uuid4().hex[:16]
        self.db._execute(
            """INSERT INTO tt_sessions (id, entity_id, tag_id, start_time) 
               VALUES (%s, %s, %s, NOW())""",
            (session_id, entity_id, tag_id)
        )
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.db._execute("SELECT * FROM tt_sessions WHERE id = %s", (session_id,), fetch='one')

    def stop_session(self, session_id: str, entity_id: str, end_time: Optional[datetime] = None) -> Optional[dict]:
        if end_time:
            self.db._execute(
                "UPDATE tt_sessions SET end_time = %s WHERE id = %s AND entity_id = %s AND end_time IS NULL",
                (end_time, session_id, entity_id)
            )
        else:
            self.db._execute(
                "UPDATE tt_sessions SET end_time = NOW() WHERE id = %s AND entity_id = %s AND end_time IS NULL",
                (session_id, entity_id)
            )
        return self.get_session(session_id)

    def add_past_session(self, entity_id: str, tag_id: str, duration_mins: int, note: str) -> dict:
        session_id = uuid.uuid4().hex[:16]
        self.db._execute(
            """INSERT INTO tt_sessions (id, entity_id, tag_id, start_time, end_time, note) 
               VALUES (%s, %s, %s, NOW() - INTERVAL '%s minutes', NOW(), %s)""",
            (session_id, entity_id, tag_id, duration_mins, note)
        )
        return self.get_session(session_id)

    def update_session_note(self, session_id: str, entity_id: str, note: str) -> Optional[dict]:
        self.db._execute(
            "UPDATE tt_sessions SET note = %s WHERE id = %s AND entity_id = %s",
            (note, session_id, entity_id)
        )
        return self.get_session(session_id)

    def get_active_sessions(self, entity_id: str) -> List[dict]:
        return self.db._execute(
            "SELECT * FROM tt_sessions WHERE entity_id = %s AND end_time IS NULL",
            (entity_id,), fetch='all'
        ) or []

    def get_stats(self, entity_id: str, start_dt: str = None, end_dt: str = None) -> List[dict]:
        query = """SELECT s.*, t.name as tag_name, t.color as tag_color 
                   FROM tt_sessions s 
                   JOIN tt_tags t ON s.tag_id = t.id 
                   WHERE s.entity_id = %s AND s.end_time IS NOT NULL"""
        params = [entity_id]
        
        if start_dt:
            query += " AND s.start_time >= %s"
            params.append(start_dt)
        if end_dt:
            query += " AND s.start_time <= %s"
            params.append(end_dt)
            
        query += " ORDER BY s.start_time ASC"
        return self.db._execute(query, tuple(params), fetch='all') or []

    def get_today_stats(self, entity_id: str) -> List[dict]:
        return self.db._execute(
            """SELECT tag_id, SUM(EXTRACT(EPOCH FROM (end_time - start_time))) * 1000 as duration_ms
               FROM tt_sessions 
               WHERE entity_id = %s 
                 AND end_time IS NOT NULL 
                 AND start_time >= CURRENT_DATE
               GROUP BY tag_id""",
            (entity_id,), fetch='all'
        ) or []
