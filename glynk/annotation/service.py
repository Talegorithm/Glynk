"""
AnnotationService - 标注的 CRUD + 向量索引

不含任何 LLM 逻辑。
"""
from uuid import uuid4

from glynk.models import Annotation, expand_span_id
from glynk.config import EmbeddingConfig
from glynk.embedding.service import generate_embedding, generate_embeddings
from glynk.annotation.vector_store import VectorStore
from glynk.storage.postgres import PostgresStore


class AnnotationService:

    EMBEDDING_TYPES = {'highlight', 'hook', 'note', 'topic', 'summary'}

    def __init__(self, db: PostgresStore, vector_store: VectorStore,
                 embedding_config: EmbeddingConfig):
        self.db = db
        self.vector_store = vector_store
        self.embedding_config = embedding_config

    @staticmethod
    def _expand_anchor_spans(ann: Annotation):
        """补全 anchor.spans 中的短 span ID（AI view 产出的 0-p6-s2 → content_id-0-p6-s2）"""
        anchor = ann.anchor
        if not anchor or not ann.content_id:
            return
        spans = anchor.get('spans', [])
        if spans:
            anchor['spans'] = [expand_span_id(s, ann.content_id) for s in spans]
        # Also expand startSpanId / endSpanId if present
        for key in ('startSpanId', 'endSpanId'):
            if key in anchor:
                anchor[key] = expand_span_id(anchor[key], ann.content_id)

    async def create(self, annotation: Annotation) -> Annotation:
        if not annotation.id:
            annotation.id = f"ann-{uuid4().hex[:12]}"
        self._expand_anchor_spans(annotation)

        vector = None
        if annotation.type in self.EMBEDDING_TYPES:
            vector = await generate_embedding(annotation.text, self.embedding_config)

        self.db.create_annotation(annotation, embedding=vector)
        return annotation

    async def create_batch(self, annotations: list[Annotation]) -> list[Annotation]:
        for ann in annotations:
            if not ann.id:
                ann.id = f"ann-{uuid4().hex[:12]}"
            self._expand_anchor_spans(ann)

        need_embedding = [a for a in annotations if a.type in self.EMBEDDING_TYPES]
        no_embedding = [a for a in annotations if a.type not in self.EMBEDDING_TYPES]

        vectors = {}
        if need_embedding:
            texts = [a.text for a in need_embedding]
            vecs = await generate_embeddings(texts, self.embedding_config)
            vectors = {a.id: v for a, v in zip(need_embedding, vecs)}

        all_vectors = [vectors.get(a.id) for a in annotations]
        self.db.create_annotations_batch(annotations, embeddings=all_vectors)

        return annotations

    def get_by_content(self, content_id: str, uid: str = None) -> list[dict]:
        return self.db.get_annotations(content_id=content_id, uid=uid)

    def get_by_uid(self, uid: str, content_id: str = None,
                   type: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        return self.db.get_user_annotations(
            uid=uid, content_id=content_id, type=type,
            limit=limit, offset=offset,
        )

    def count_by_uid(self, uid: str, content_id: str = None, type: str = None) -> int:
        return self.db.count_user_annotations(uid=uid, content_id=content_id, type=type)

    def delete(self, ann_id: str, uid: str) -> bool:
        return self.db.delete_annotation(ann_id, uid)

    def update(self, ann_id: str, uid: str, **kwargs) -> dict | None:
        return self.db.update_annotation(ann_id, uid, **kwargs)

    async def search_user_annotations(self, uid: str, query: str, top_k: int = 10) -> list[dict]:
        vector = await generate_embedding(query, self.embedding_config)
        return await self.vector_store.search(
            vector=vector, top_k=top_k,
            filters={"uid": uid, "include_private": True},
        )
