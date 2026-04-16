"""
VectorStore - pgvector on units table

搜索有 vector 的 Units（annotation source units）。
"""
from typing import Protocol
from glynk.storage.postgres import PostgresStore


class VectorStore(Protocol):
    async def search(self, vector: list[float], top_k: int,
                     filters: dict = None) -> list[dict]:
        ...


class PgVectorStore:
    """pgvector on units table."""

    def __init__(self, db: PostgresStore):
        self.db = db

    async def search(self, vector: list[float], top_k: int,
                     filters: dict = None) -> list[dict]:
        conditions = ["u.vector IS NOT NULL"]
        params = [str(vector)]

        if filters:
            if "roles" in filters:
                roles = filters["roles"] if isinstance(filters["roles"], list) else [filters["roles"]]
                conditions.append("u.metadata->>'role' = ANY(%s)")
                params.append(roles)

            if "unit_ids" in filters:
                # Filter by target_unit through anchors
                conditions.append("""
                    u.id IN (SELECT a.source_unit FROM anchors a
                             WHERE a.target_unit = ANY(%s))
                """)
                params.append(filters["unit_ids"])

            if "entity_id" in filters and filters.get("include_private"):
                conditions.append("(u.visibility->>'type' = 'public' OR u.author_id = %s)")
                params.append(filters["entity_id"])
            else:
                conditions.append("u.visibility->>'type' = 'public'")
        else:
            conditions.append("u.visibility->>'type' = 'public'")

        where = "WHERE " + " AND ".join(conditions)

        sql = f"""
            SELECT u.id, u.body, u.metadata, u.author_id, u.created_at,
                   1 - (u.vector <=> %s::vector) as score,
                   a.target_unit as content_id, a.target_span, a.role, a.metadata as anchor_metadata
            FROM units u
            LEFT JOIN anchors a ON a.source_unit = u.id
            {where}
            ORDER BY u.vector <=> %s::vector
            LIMIT {top_k}
        """
        params.append(str(vector))

        return self.db.execute_query(sql, tuple(params))
