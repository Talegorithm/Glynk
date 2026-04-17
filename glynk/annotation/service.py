"""
AnchorService - Anchor + Unit CRUD + 向量索引

创建 Anchor 时，如果有 body，同时创建一个 source Unit。
Role 的 (source, target, body) 约束见 models.ROLE_SCHEMAS。
"""
from uuid import uuid4

from glynk.models import expand_span_id, validate_anchor
from glynk.config import EmbeddingConfig
from glynk.embedding.service import (
    generate_embedding, generate_embeddings, maybe_embed, should_embed,
)
from glynk.annotation.vector_store import VectorStore
from glynk.storage.postgres import PostgresStore


class AnchorService:

    def __init__(self, db: PostgresStore, vector_store: VectorStore,
                 embedding_config: EmbeddingConfig):
        self.db = db
        self.vector_store = vector_store
        self.embedding_config = embedding_config

    async def create(self, entity_id: str, target_unit: str, role: str,
                     target_span: str = None, metadata: dict = None,
                     text: str = "", tags: list[str] = None,
                     visibility: str = "public",
                     in_reply_to: str | None = None) -> dict:
        """
        创建 Anchor。如果 text 非空，先创建 source Unit。

        Role 的合法 (source_type, target_type, body) 组合由 ROLE_SCHEMAS 定义。
        不合法的组合直接 ValueError。

        Reply 语义：当 role='reply' 且 in_reply_to 非空时，把父 reply 的 Unit id
        写入 anchor.metadata.in_reply_to —— 前端据此构建 thread 树。`target_span`
        仍指向原文话题锚点，使"某 span 下所有 reply" 是一次 O(1) 过滤查询。

        返回 {anchor_id, source_unit_id, ...}
        """
        metadata = metadata or {}
        tags = tags or []

        # Expand short span IDs in metadata
        self._expand_metadata_spans(metadata, target_unit)
        if target_span:
            target_span = expand_span_id(target_span, target_unit)

        # Thread parent pointer lives in metadata, not as a separate anchor
        if role == 'reply' and in_reply_to:
            metadata['in_reply_to'] = in_reply_to

        # Determine source/target types, then validate before creating anything
        source_type = 'unit' if text else 'entity'
        target_type = 'span' if target_span else 'unit'
        validate_anchor(role, source_type, target_type, has_body=bool(text))

        source_unit_id = None
        if text:
            # Create source Unit for the annotation body
            source_unit_id = f"ann-{uuid4().hex[:12]}"
            unit_metadata = {"tags": tags, "role": role}
            vector = await maybe_embed(text, self.embedding_config, unit_metadata)

            self.db.create_unit(
                unit_id=source_unit_id,
                author_id=entity_id,
                origin='authored',
                shape='flat',
                body={"html": text},
                visibility={"type": visibility},
                metadata=unit_metadata,
                vector=vector,
                vector_text=text,
            )

        anchor_id = f"anc-{uuid4().hex[:12]}"
        self.db.create_anchor(
            anchor_id=anchor_id,
            source_type=source_type,
            source_unit=source_unit_id,
            source_entity=entity_id if source_type == 'entity' else None,
            target_type=target_type,
            target_unit=target_unit,
            target_span=target_span,
            role=role,
            metadata=metadata,
        )

        return {
            "anchor_id": anchor_id,
            "source_unit_id": source_unit_id,
            "id": anchor_id,
            "role": role,
            "target_unit": target_unit,
            "target_span": target_span,
            "metadata": metadata,
            "text": text,
            "tags": tags,
        }

    async def create_batch(self, entity_id: str, items: list[dict]) -> list[dict]:
        """批量创建 Anchors + source Units。每条按 ROLE_SCHEMAS 校验。"""
        # Pre-pass: normalize + validate each item. Fail fast on invalid input.
        normalized: list[dict] = []
        for i, item in enumerate(items):
            metadata = item.get('metadata', {}) or {}
            target_unit = item['target_unit']
            target_span = item.get('target_span')
            role = item['role']
            text = item.get('text', '') or ''
            tags = item.get('tags', []) or []
            visibility = item.get('visibility', 'public')

            self._expand_metadata_spans(metadata, target_unit)
            if target_span:
                target_span = expand_span_id(target_span, target_unit)

            source_type = 'unit' if text else 'entity'
            target_type = 'span' if target_span else 'unit'
            try:
                validate_anchor(role, source_type, target_type, has_body=bool(text))
            except ValueError as e:
                raise ValueError(f"anchors[{i}]: {e}") from e

            normalized.append({
                'i': i, 'role': role, 'text': text, 'tags': tags,
                'visibility': visibility, 'metadata': metadata,
                'source_type': source_type, 'target_type': target_type,
                'target_unit': target_unit, 'target_span': target_span,
            })

        # Embedding：批量调 Azure。只对通过 should_embed 的 text 排队。
        texts_to_embed: list[str] = []
        item_indices: list[int] = []
        for n in normalized:
            if n['text'] and should_embed(n['text'], {'tags': n['tags'], 'role': n['role']}):
                texts_to_embed.append(n['text'])
                item_indices.append(n['i'])

        vectors: dict[int, list | None] = {}
        if texts_to_embed:
            vecs = await generate_embeddings(texts_to_embed, self.embedding_config)
            for idx, vec in zip(item_indices, vecs):
                vectors[idx] = vec

        units_to_create = []
        anchors_to_create = []
        results = []

        for n in normalized:
            source_unit_id = None
            if n['text']:
                source_unit_id = f"ann-{uuid4().hex[:12]}"
                units_to_create.append({
                    'id': source_unit_id,
                    'author_id': entity_id,
                    'origin': 'authored',
                    'shape': 'flat',
                    'body': {"html": n['text']},
                    'visibility': {"type": n['visibility']},
                    'metadata': {"tags": n['tags'], "role": n['role']},
                    'vector_text': n['text'],
                })

            anchor_id = f"anc-{uuid4().hex[:12]}"
            anchors_to_create.append({
                'id': anchor_id,
                'source_type': n['source_type'],
                'source_unit': source_unit_id,
                'source_entity': entity_id if n['source_type'] == 'entity' else None,
                'target_type': n['target_type'],
                'target_unit': n['target_unit'],
                'target_span': n['target_span'],
                'role': n['role'],
                'metadata': n['metadata'],
            })
            results.append({"anchor_id": anchor_id, "source_unit_id": source_unit_id})

        # Batch insert: unit_vectors 顺序必须和 units_to_create 对齐
        unit_vectors = [vectors.get(n['i']) for n in normalized if n['text']]

        if units_to_create:
            self.db.create_units_batch(units_to_create, vectors=unit_vectors)
        if anchors_to_create:
            self.db.create_anchors_batch(anchors_to_create)

        return results

    def get_for_unit(self, target_unit: str, entity_id: str = None) -> list[dict]:
        """Get anchors for a unit, formatted for frontend compatibility."""
        raw = self.db.get_anchors_for_unit(target_unit, entity_id=entity_id)
        return [self._format_anchor(r) for r in raw]

    def get_by_entity(self, entity_id: str, target_unit: str = None,
                      role: str = None, limit: int = 50, offset: int = 0):
        """Get user's anchors, formatted for frontend compatibility."""
        raw = self.db.get_anchors_by_entity(
            entity_id, target_unit=target_unit, role=role,
            limit=limit, offset=offset,
        )
        total = self.db.count_anchors_by_entity(
            entity_id, target_unit=target_unit, role=role,
        )
        return [self._format_anchor(r) for r in raw], total

    def delete(self, anchor_id: str, entity_id: str) -> bool:
        return self.db.delete_anchor(anchor_id, entity_id)

    async def update(self, anchor_id: str, entity_id: str,
                     text: str = None, metadata: dict = None) -> dict | None:
        """Update anchor and/or its source unit."""
        if metadata is not None:
            result = self.db.update_anchor(anchor_id, entity_id, metadata=metadata)
            if not result:
                return None

        if text is not None:
            # Find the anchor to get source_unit
            # We need to update the source unit's body
            anchor = self.db._execute(
                "SELECT * FROM anchors WHERE id = %s", (anchor_id,), fetch='one'
            )
            if anchor and anchor.get('source_unit'):
                self.db.update_unit(
                    anchor['source_unit'],
                    body={"html": text},
                )

        return {"ok": True, "id": anchor_id}

    async def search_user_anchors(self, entity_id: str, query: str, top_k: int = 10) -> list[dict]:
        vector = await generate_embedding(query, self.embedding_config)
        raw = await self.vector_store.search(
            vector=vector, top_k=top_k,
            filters={"entity_id": entity_id, "include_private": True},
        )
        # Format into frontend-compatible annotation shape
        return [self._format_search_result(r) for r in raw]

    @staticmethod
    def _format_search_result(raw: dict) -> dict:
        """Format vector search result into frontend-compatible annotation."""
        body = raw.get('body') or {}
        meta = raw.get('metadata') or {}
        anchor_meta = raw.get('anchor_metadata') or {}

        return {
            "id": raw.get("id", ""),
            "content_id": raw.get("content_id", ""),
            "anchor": anchor_meta,
            "type": raw.get("role", ""),
            "text": body.get("html", ""),
            "tags": meta.get("tags", []),
            "contextuality": meta.get("contextuality", "standalone"),
            "source": "human",
            "visibility": "public",
            "created_at": raw.get("created_at"),
            "target_span": raw.get("target_span"),
            "score": raw.get("score"),
        }

    @staticmethod
    def _expand_metadata_spans(metadata: dict, target_unit: str):
        """Expand short span IDs in metadata."""
        if not metadata or not target_unit:
            return
        for key in ('spans', ):
            if key in metadata:
                metadata[key] = [expand_span_id(s, target_unit) for s in metadata[key]]
        for key in ('startSpanId', 'endSpanId'):
            if key in metadata:
                metadata[key] = expand_span_id(metadata[key], target_unit)

    @staticmethod
    def _format_anchor(raw: dict) -> dict:
        """Format raw DB row into frontend-compatible annotation format."""
        source_body = raw.get('source_body') or {}
        source_meta = raw.get('source_metadata') or {}
        anchor_meta = raw.get('metadata') or {}
        target_meta = raw.get('target_metadata') or {}

        return {
            "id": raw["id"],
            "content_id": raw.get("target_unit", ""),
            "source_unit": raw.get("source_unit", ""),
            "anchor": anchor_meta,
            "type": raw.get("role", ""),
            "text": source_body.get("html", ""),
            "tags": source_meta.get("tags", []),
            "contextuality": source_meta.get("contextuality", "standalone"),
            "source": "human",
            "visibility": (raw.get("source_visibility") or {}).get("type", "public"),
            "created_at": raw.get("created_at"),
            # Extra fields
            "target_span": raw.get("target_span"),
            "author_name": raw.get("author_name", ""),
            "author_id": raw.get("author_id", raw.get("source_entity", "")),
            "content_title": target_meta.get("title", ""),
        }
