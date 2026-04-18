"""
RetrievalEngine - 语义检索引擎

命中的永远是 Unit（有 vector 的那条）。如果这个 Unit 是某条 Anchor 的 source，
结果里附带 anchor 信息 + `default_view` 提示前端怎么展示。否则是 standalone Unit，
anchor 为 null。
"""
import math
from uuid import uuid4

from glynk.models import QueryRequest, QueryResponse, parse_file_idx_from_span
from glynk.config import EmbeddingConfig
from glynk.embedding.service import generate_embedding
from glynk.annotation.vector_store import VectorStore
from glynk.storage.postgres import PostgresStore


# Roles where the "click action" should jump to the target passage (原文语境
# 是主角). 其他 role（note / summary / reply / hook）的 source Unit text 本身
# 就是主要内容，展示时以 Unit 为主。
TARGET_VIEW_ROLES = {"highlight"}


def _default_view(role: str | None) -> str:
    """'target' = 跳原文 / 'unit' = 显示 Unit 本身。"""
    if role and role in TARGET_VIEW_ROLES:
        return "target"
    return "unit"


class RetrievalEngine:

    def __init__(self, db: PostgresStore, vector_store: VectorStore,
                 embedding_config: EmbeddingConfig):
        self.db = db
        self.vector_store = vector_store
        self.embedding_config = embedding_config

    async def query(self, request: QueryRequest) -> QueryResponse:
        vector = await generate_embedding(request.text, self.embedding_config)
        if vector is None:
            raise RuntimeError(
                "Embedding unavailable (AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT "
                "not configured or request failed). Semantic search requires embeddings."
            )

        filters: dict = {}
        if request.roles:
            # 传了 roles：只搜有 anchor 且 role 匹配的 Unit，standalone 排除
            filters["roles"] = request.roles
        if request.unit_ids:
            filters["unit_ids"] = request.unit_ids
        if request.entity_id:
            filters["entity_id"] = request.entity_id
            filters["include_private"] = True

        raw_results = await self.vector_store.search(
            vector=vector, top_k=request.top_k, filters=filters,
        )

        results = self._enrich_results(raw_results)
        results = self._rerank_with_crowd_signal(results)

        query_id = f"qry-{uuid4().hex[:12]}"

        if request.entity_id:
            self.db.log_event(
                event_id=f"evt-{uuid4().hex[:12]}",
                actor_id=request.entity_id,
                event_type='search',
                payload={"query": request.text, "result_count": len(results)},
            )

        for r in results:
            role = r.get("role")
            dv = _default_view(role)
            r["default_view"] = dv

            # target: 如果这个 Unit 是某条 anchor 的 source，记录它指向的"原文位置"。
            # null = standalone Unit（纯 authored 想法，没挂到任何内容上）。
            # 名字故意不用 "anchor"，因为 anchor_metadata 字段已经在用这个词了。
            content_id = r.get("content_id")
            target_span = r.get("target_span")
            if content_id:
                r["target"] = {
                    "role": role,
                    "unit": content_id,
                    "span": target_span,
                }
            else:
                r["target"] = None

            # browse_url：只要 Unit 挂到了某个 target，点击都去看那个 target 的上下文——
            # 用户用这个卡片的主要 action 永远是"去原文看看"。default_view 只影响卡片
            # 怎么渲染（target 视角把原文作为主角；unit 视角把 Unit 本身作为主角、target
            # 作为"在 XX 上"的尾注）。没 target 的 standalone Unit 指向 /u/{id}（路由待建）。
            if content_id:
                file_idx = parse_file_idx_from_span(target_span or "")
                spans = (r.get("anchor_metadata") or {}).get("spans", [])
                loc = target_span or (spans[0] if spans else "")
                r["browse_url"] = f"/read/{content_id}/{file_idx}?loc={loc}&qid={query_id}"
            else:
                r["browse_url"] = f"/u/{r.get('id')}?qid={query_id}"

        return QueryResponse(query_id=query_id, results=results)

    def _enrich_results(self, raw_results: list[dict]) -> list[dict]:
        content_cache: dict = {}
        for r in raw_results:
            cid = r.get("content_id")
            if cid and cid not in content_cache:
                content_cache[cid] = self.db.get_unit(cid) or {}

            content = content_cache.get(cid, {}) or {}
            meta = content.get("metadata") or {}
            r["content_title"] = meta.get("title", "")
            r["content_author"] = content.get("author_name", "")
            r["text"] = (r.get("body") or {}).get("html", "")
            r["tags"] = (r.get("metadata") or {}).get("tags", [])
            r["type"] = r.get("role", "") or ""
            # 兼容：frontend 里有地方直接读 r.anchor.spans（= anchor metadata 的字段）。
            # 不要和 r.target 混淆 —— r.target 是 anchor 指向的原文位置.
            r["anchor"] = r.get("anchor_metadata") or {}

        return raw_results

    def _rerank_with_crowd_signal(self, results: list[dict]) -> list[dict]:
        for r in results:
            target_span = r.get("target_span", "")
            crowd = self.db.get_span_crowd_count(target_span) if target_span else 0
            r["crowd_count"] = crowd
            score = r.get("score", 0) or 0
            r["final_score"] = score * 0.8 + min(math.log(crowd + 1) / 5, 1.0) * 0.2

        results.sort(key=lambda r: r.get("final_score", 0), reverse=True)
        return results
