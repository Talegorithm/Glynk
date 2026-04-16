"""
RetrievalEngine - 语义检索引擎

搜索 Units 的 vector 字段，通过 Anchors 关联到目标内容。
"""
import math
from uuid import uuid4

from glynk.models import QueryRequest, QueryResponse, parse_file_idx_from_span
from glynk.config import EmbeddingConfig
from glynk.embedding.service import generate_embedding
from glynk.annotation.vector_store import VectorStore
from glynk.storage.postgres import PostgresStore


class RetrievalEngine:

    def __init__(self, db: PostgresStore, vector_store: VectorStore,
                 embedding_config: EmbeddingConfig):
        self.db = db
        self.vector_store = vector_store
        self.embedding_config = embedding_config

    async def query(self, request: QueryRequest) -> QueryResponse:
        vector = await generate_embedding(request.text, self.embedding_config)

        filters = {}
        if request.roles:
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

        # Log event
        if request.entity_id:
            self.db.log_event(
                event_id=f"evt-{uuid4().hex[:12]}",
                actor_id=request.entity_id,
                event_type='search',
                payload={"query": request.text, "result_count": len(results)},
            )

        for r in results:
            spans = (r.get("anchor_metadata") or {}).get("spans", [])
            span_id = r.get("target_span") or (spans[0] if spans else "")
            file_idx = parse_file_idx_from_span(span_id)
            content_id = r.get("content_id", "")
            r["browse_url"] = f"/read/{content_id}/{file_idx}?loc={span_id}&qid={query_id}"

        return QueryResponse(query_id=query_id, results=results)

    def _enrich_results(self, raw_results: list[dict]) -> list[dict]:
        content_cache = {}
        for r in raw_results:
            cid = r.get("content_id")
            if cid and cid not in content_cache:
                content_cache[cid] = self.db.get_unit(cid)

            content = content_cache.get(cid, {}) or {}
            meta = content.get("metadata") or {}
            r["content_title"] = meta.get("title", "")
            r["content_author"] = content.get("author_name", "")
            r["text"] = (r.get("body") or {}).get("html", "")
            r["tags"] = (r.get("metadata") or {}).get("tags", [])
            r["type"] = r.get("role", "")
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
