"""
标注 API

POST /annotate          创建标注
POST /annotate/batch    批量创建
POST /query             语义检索
GET  /annotations       用户标注历史
POST /annotations/search 语义搜索用户标注
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user, get_optional_user
from glynk.models import Annotation, QueryRequest
from glynk.annotation.service import AnnotationService
from glynk.annotation.search import RetrievalEngine

router = APIRouter(tags=["annotations"])

_annotation_service: Optional[AnnotationService] = None
_retrieval_engine: Optional[RetrievalEngine] = None


def set_services(annotation_service: AnnotationService, retrieval_engine: RetrievalEngine):
    global _annotation_service, _retrieval_engine
    _annotation_service = annotation_service
    _retrieval_engine = retrieval_engine


class AnnotateRequest(BaseModel):
    content_id: str
    anchor: dict
    type: str
    text: str
    tags: list[str] = []
    contextuality: str = "standalone"
    visibility: str = "public"


class BatchAnnotateRequest(BaseModel):
    annotations: list[AnnotateRequest]


class QueryRequestModel(BaseModel):
    text: str
    user_context: dict | None = None
    types: list[str] | None = None
    content_ids: list[str] | None = None
    top_k: int = 10


class SearchRequest(BaseModel):
    query: str


@router.post("/annotate", status_code=201)
async def create_annotation(req: AnnotateRequest, user: dict = Depends(get_current_user)):
    """创建单条标注"""
    if _annotation_service is None:
        raise HTTPException(500, "Service not initialized")

    ann = Annotation(
        id="",
        content_id=req.content_id,
        anchor=req.anchor,
        type=req.type,
        text=req.text,
        tags=req.tags,
        contextuality=req.contextuality,
        source="human",
        uid=user["uid"],
        visibility=req.visibility,
    )

    result = await _annotation_service.create(ann)
    return {
        "id": result.id,
        "content_id": result.content_id,
        "type": result.type,
        "text": result.text,
        "anchor": result.anchor,
        "tags": result.tags,
    }


@router.post("/annotate/batch", status_code=201)
async def create_batch(req: BatchAnnotateRequest, user: dict = Depends(get_current_user)):
    """批量创建标注"""
    if _annotation_service is None:
        raise HTTPException(500, "Service not initialized")

    annotations = [
        Annotation(
            id="",
            content_id=a.content_id,
            anchor=a.anchor,
            type=a.type,
            text=a.text,
            tags=a.tags,
            contextuality=a.contextuality,
            source="human",
            uid=user["uid"],
            visibility=a.visibility,
        )
        for a in req.annotations
    ]

    results = await _annotation_service.create_batch(annotations)
    return {
        "created": len(results),
        "ids": [r.id for r in results],
    }


@router.post("/query")
async def query_annotations(req: QueryRequestModel,
                            user: dict = Depends(get_optional_user)):
    """语义检索标注"""
    if _retrieval_engine is None:
        raise HTTPException(500, "Service not initialized")

    query_req = QueryRequest(
        text=req.text,
        user_context=req.user_context,
        types=req.types or ["highlight", "hook"],
        content_ids=req.content_ids,
        uid=user["uid"] if user else None,
        top_k=req.top_k,
    )

    response = await _retrieval_engine.query(query_req)
    return {
        "query_id": response.query_id,
        "results": response.results,
    }


@router.get("/annotations")
async def get_user_annotations(
    content_id: str = None,
    type: str = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """获取用户自己的标注历史"""
    if _annotation_service is None:
        raise HTTPException(500, "Service not initialized")

    annotations = _annotation_service.get_by_uid(
        uid=user["uid"],
        content_id=content_id,
        type=type,
        limit=limit,
        offset=offset,
    )
    total = _annotation_service.count_by_uid(
        uid=user["uid"],
        content_id=content_id,
        type=type,
    )

    return {"annotations": annotations, "total": total}


class UpdateAnnotationRequest(BaseModel):
    text: str | None = None
    anchor: dict | None = None


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(annotation_id: str, user: dict = Depends(get_current_user)):
    """删除标注（仅限本人）"""
    if _annotation_service is None:
        raise HTTPException(500, "Service not initialized")
    deleted = _annotation_service.delete(annotation_id, user["uid"])
    if not deleted:
        raise HTTPException(404, "Annotation not found or not owned by you")
    return {"ok": True}


@router.patch("/annotations/{annotation_id}")
async def update_annotation(annotation_id: str, req: UpdateAnnotationRequest,
                            user: dict = Depends(get_current_user)):
    """更新标注（仅限本人）"""
    if _annotation_service is None:
        raise HTTPException(500, "Service not initialized")
    updates = {}
    if req.text is not None:
        updates["text"] = req.text
    if req.anchor is not None:
        updates["anchor"] = req.anchor
    if not updates:
        raise HTTPException(400, "Nothing to update")
    result = _annotation_service.update(annotation_id, user["uid"], **updates)
    if not result:
        raise HTTPException(404, "Annotation not found or not owned by you")
    return result


@router.post("/annotations/search")
async def search_user_annotations(req: SearchRequest,
                                  user: dict = Depends(get_current_user)):
    """语义搜索用户的标注"""
    if _annotation_service is None:
        raise HTTPException(500, "Service not initialized")

    results = await _annotation_service.search_user_annotations(
        uid=user["uid"],
        query=req.query,
    )
    return {"results": results}
