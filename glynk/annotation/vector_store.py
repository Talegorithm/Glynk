"""
VectorStore 协议 + PgVectorStore 实现

pgvector 直接在 annotations 表上做向量搜索。
"""
from typing import Protocol, Optional
from glynk.storage.postgres import PostgresStore


class VectorStore(Protocol):
    async def search(self, vector: list[float], top_k: int,
                     filters: dict = None) -> list[dict]:
        ...


class PgVectorStore:
    """pgvector 实现。直接在 annotations 表上做向量搜索。"""

    def __init__(self, db: PostgresStore):
        self.db = db

    async def search(self, vector: list[float], top_k: int,
                     filters: dict = None) -> list[dict]:
        conditions = ["embedding IS NOT NULL"]
        params = [str(vector)]

        if filters:
            if "type" in filters:
                types = filters["type"] if isinstance(filters["type"], list) else [filters["type"]]
                conditions.append(f"type = ANY(%s)")
                params.append(types)

            if "content_ids" in filters:
                conditions.append(f"content_id = ANY(%s)")
                params.append(filters["content_ids"])

            if "uid" in filters and filters.get("include_private"):
                conditions.append(f"(visibility = 'public' OR uid = %s)")
                params.append(filters["uid"])
            else:
                conditions.append("visibility = 'public'")
        else:
            conditions.append("visibility = 'public'")

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        sql = f"""
            SELECT id, content_id, type, text, anchor, tags, source, uid,
                   contextuality, created_at,
                   1 - (embedding <=> %s::vector) as score
            FROM annotations
            {where}
            ORDER BY embedding <=> %s::vector
            LIMIT {top_k}
        """
        # The first %s is for score calculation, need to add vector again for ORDER BY
        params.append(str(vector))

        return self.db.execute_query(sql, tuple(params))
