"""
RetrievalEngine - 语义检索引擎

通过 VectorStore 抽象层搜索，支持众包信号重排序。
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
        # 1. 生成查询向量
        vector = await generate_embedding(request.text, self.embedding_config)

        # 2. 构建过滤条件
        filters = {}
        if request.types:
            filters["type"] = request.types
        if request.content_ids:
            filters["content_ids"] = request.content_ids
        if request.uid:
            filters["uid"] = request.uid
            filters["include_private"] = True
        if request.version:
            filters["version"] = request.version

        # 3. 向量搜索
        raw_results = await self.vector_store.search(
            vector=vector, top_k=request.top_k, filters=filters,
        )

        # 4. 补全内容元数据
        results = self._enrich_results(raw_results)

        # 5. 众包信号重排序
        results = self._rerank_with_crowd_signal(results)

        # 6. 记录查询
        query_id = f"qry-{uuid4().hex[:12]}"
        self.db.create_query(
            query_id, request.uid,
            request.user_context,
            request.text,
            [r["id"] for r in results],
        )

        # 7. 构造 browse_url
        for r in results:
            spans = r.get("anchor", {}).get("spans", [])
            span_id = spans[0] if spans else ""
            file_idx = parse_file_idx_from_span(span_id)
            r["browse_url"] = f"/browse/{r['content_id']}/{file_idx}?loc={span_id}&qid={query_id}"

        return QueryResponse(query_id=query_id, results=results)

    def _enrich_results(self, raw_results: list[dict]) -> list[dict]:
        """补全内容元数据（title, author等）"""
        content_cache = {}
        for r in raw_results:
            cid = r.get("content_id")
            if cid and cid not in content_cache:
                content_cache[cid] = self.db.get_content(cid)

            content = content_cache.get(cid, {}) or {}
            r["content_title"] = content.get("title", "")
            r["content_author"] = content.get("author", "")

        return raw_results

    def _rerank_with_crowd_signal(self, results: list[dict]) -> list[dict]:
        """用众包信号加权排序"""
        for r in results:
            spans = r.get("anchor", {}).get("spans", [])
            span_id = spans[0] if spans else ""
            crowd = self.db.get_span_crowd_count(span_id) if span_id else 0
            r["crowd_count"] = crowd
            score = r.get("score", 0) or 0
            r["final_score"] = score * 0.8 + min(math.log(crowd + 1) / 5, 1.0) * 0.2

        results.sort(key=lambda r: r.get("final_score", 0), reverse=True)
        return results
