"""
VectorStore - pgvector on units table

搜索有 vector 的 Units。可选按 anchor.role 过滤（通过 LEFT JOIN），
没传 roles 时连没 anchor 的 standalone Units 也一起返回。
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
        """
        filters (全部可选):
          roles:             list[str] —— anchor.role 白名单。传了就只返回有 anchor 且 role 匹配的
                                         Unit; 不传 → 返回所有 Unit (含 standalone)
          unit_ids:          list[str] —— 限定在这些 target_unit 的标注里搜
          entity_id + include_private: 默认只搜 public, 设了就加自己的 private
        """
        filters = filters or {}

        conditions = ["u.vector IS NOT NULL"]
        params: list = [str(vector)]

        roles = filters.get("roles")
        if roles:
            # 传了 roles → 只要 a 有行且 role 匹配
            conditions.append("a.role = ANY(%s)")
            params.append(roles)

        if "unit_ids" in filters:
            conditions.append("a.target_unit = ANY(%s)")
            params.append(filters["unit_ids"])

        if filters.get("entity_id") and filters.get("include_private"):
            conditions.append("(u.visibility->>'type' = 'public' OR u.author_id = %s)")
            params.append(filters["entity_id"])
        else:
            conditions.append("u.visibility->>'type' = 'public'")

        where = " AND ".join(conditions)

        sql = f"""
            SELECT u.id, u.body, u.metadata, u.author_id, u.created_at,
                   1 - (u.vector <=> %s::vector) as score,
                   a.target_unit as content_id, a.target_span, a.role,
                   a.metadata as anchor_metadata
            FROM units u LEFT JOIN anchors a ON a.source_unit = u.id
            WHERE {where}
            ORDER BY u.vector <=> %s::vector
            LIMIT {top_k}
        """
        params.append(str(vector))

        return self.db.execute_query(sql, tuple(params))
