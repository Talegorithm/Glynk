"""
Anchor API (replaces annotation_router)

POST   /anchors            创建 Anchor (+ optional source Unit)
POST   /anchors/batch      批量创建
GET    /anchors             查询（按 target_unit / role / entity 过滤）
PATCH  /anchors/{id}       更新
DELETE /anchors/{id}       删除
POST   /anchors/search     语义搜索用户标注
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user, get_optional_user
from glynk.annotation.service import AnchorService

router = APIRouter(tags=["anchors"])

_anchor_service: Optional[AnchorService] = None


def set_services(anchor_service: AnchorService, retrieval_engine=None):
    global _anchor_service
    _anchor_service = anchor_service


class CreateAnchorRequest(BaseModel):
    target_unit: str
    target_span: str | None = None
    role: str                         # highlight | hook | note | reaction | reply | ...
    metadata: dict = {}               # color, offsets, spans, ...
    text: str = ""                    # creates a source Unit if non-empty
    tags: list[str] = []
    visibility: str = "public"
    in_reply_to: str | None = None    # 当 role=reply 时，被回复的 Unit ID；会额外创建 role=reply_to 的 anchor


class BatchCreateRequest(BaseModel):
    anchors: list[CreateAnchorRequest]


class UpdateAnchorRequest(BaseModel):
    text: str | None = None
    metadata: dict | None = None


class SearchRequest(BaseModel):
    query: str


@router.post("/anchors", status_code=201)
async def create_anchor(req: CreateAnchorRequest, user: dict = Depends(get_current_user)):
    """创建 Anchor（如果有 text，同时创建 source Unit）"""
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")

    result = await _anchor_service.create(
        entity_id=user["entity_id"],
        target_unit=req.target_unit,
        target_span=req.target_span,
        role=req.role,
        metadata=req.metadata,
        text=req.text,
        tags=req.tags,
        visibility=req.visibility,
        in_reply_to=req.in_reply_to,
    )
    return result


@router.post("/anchors/batch", status_code=201)
async def create_batch(req: BatchCreateRequest, user: dict = Depends(get_current_user)):
    """批量创建"""
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")

    results = await _anchor_service.create_batch(
        entity_id=user["entity_id"],
        items=[{
            "target_unit": a.target_unit,
            "target_span": a.target_span,
            "role": a.role,
            "metadata": a.metadata,
            "text": a.text,
            "tags": a.tags,
            "visibility": a.visibility,
        } for a in req.anchors],
    )
    return {"created": len(results), "ids": [r["anchor_id"] for r in results]}


@router.get("/anchors")
async def get_anchors(
    content_id: str = None,
    target_unit: str = None,
    role: str = None,
    type: str = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    """查询用户标注"""
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")

    # content_id is alias for target_unit, type is alias for role (frontend compat)
    tu = target_unit or content_id
    r = role or type

    annotations, total = _anchor_service.get_by_entity(
        entity_id=user["entity_id"],
        target_unit=tu,
        role=r,
        limit=limit,
        offset=offset,
    )
    return {"annotations": annotations, "total": total}


@router.get("/anchors/thread")
async def get_anchor_thread(
    content_id: str = None,
    target_unit: str = None,
    target_span: str = None,
    user: dict = Depends(get_optional_user),
):
    """获取某个 span 下的所有公开讨论和自己的回复"""
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")
        
    tu = target_unit or content_id
    if not tu:
        raise HTTPException(400, "target_unit is required")
        
    entity_id = user["entity_id"] if user else None
    anchors = _anchor_service.get_for_unit(
        target_unit=tu,
        entity_id=entity_id,
    )
    
    # Filter by target_span if provided
    if target_span:
        from glynk.models import expand_span_id
        target_span = expand_span_id(target_span, tu)
        
        # We need to include anchors that directly target this span
        # AND anchors that are replies to anchors in this thread (target_unit = any reply unit)
        # For simplicity, returning all anchors for the unit and letting frontend build tree is an option,
        # but to save bandwidth we could just filter here. Let's return all and let frontend filter/map,
        # because reply anchors target another UNIT (the parent reply), not the original span.
        # However, to be efficient, we probably just get everything for the unit 
        # or we recursively fetch. But since get_for_unit fetches all public anchors for the unit, 
        # we can just return it and let frontend filter by those rooted at target_span.
        
        return {"annotations": anchors}
    else:
        return {"annotations": anchors}



@router.delete("/anchors/{anchor_id}")
async def delete_anchor(anchor_id: str, user: dict = Depends(get_current_user)):
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")
    deleted = _anchor_service.delete(anchor_id, user["entity_id"])
    if not deleted:
        raise HTTPException(404, "Anchor not found or not owned by you")
    return {"ok": True}


@router.patch("/anchors/{anchor_id}")
async def update_anchor(anchor_id: str, req: UpdateAnchorRequest,
                        user: dict = Depends(get_current_user)):
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")

    result = await _anchor_service.update(
        anchor_id=anchor_id,
        entity_id=user["entity_id"],
        text=req.text,
        metadata=req.metadata,
    )
    if not result:
        raise HTTPException(404, "Anchor not found or not owned by you")
    return result


@router.post("/anchors/search")
async def search_anchors(req: SearchRequest, user: dict = Depends(get_current_user)):
    if _anchor_service is None:
        raise HTTPException(500, "Service not initialized")

    results = await _anchor_service.search_user_anchors(
        entity_id=user["entity_id"],
        query=req.query,
    )
    return {"results": results}
