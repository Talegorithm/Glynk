"""
RSS 源管理 API

POST   /sources        添加
GET    /sources        列出
PUT    /sources/{id}   更新
DELETE /sources/{id}   删除
"""
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user
from glynk.storage.postgres import PostgresStore

router = APIRouter(prefix="/sources", tags=["sources"])


class CreateSourceRequest(BaseModel):
    url: str
    name: str = ""
    content_type: str | None = None
    schedule: str = "daily"
    max_items: int = 5
    filters: dict | None = None


class UpdateSourceRequest(BaseModel):
    name: str | None = None
    content_type: str | None = None
    schedule: str | None = None
    max_items: int | None = None
    enabled: bool | None = None
    filters: dict | None = None


@router.post("")
async def create_source(req: CreateSourceRequest, user: dict = Depends(get_current_user)):
    """添加 RSS 源"""
    db = PostgresStore.get_instance()
    source_id = f"rss-{uuid4().hex[:12]}"

    db.create_source(
        source_id=source_id,
        url=req.url,
        name=req.name,
        content_type=req.content_type,
        schedule=req.schedule,
        max_items=req.max_items,
        filters=req.filters,
        created_by=user["uid"],
    )

    return {"id": source_id, "url": req.url}


@router.get("")
async def list_sources(user: dict = Depends(get_current_user)):
    """列出 RSS 源"""
    db = PostgresStore.get_instance()
    sources = db.list_sources(enabled_only=False)
    return {"sources": sources}


@router.put("/{source_id}")
async def update_source(source_id: str, req: UpdateSourceRequest,
                        user: dict = Depends(get_current_user)):
    """更新 RSS 源"""
    db = PostgresStore.get_instance()
    source = db.get_source(source_id)
    if not source:
        raise HTTPException(404, "Source not found")

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if updates:
        db.update_source(source_id, **updates)

    return {"ok": True}


@router.delete("/{source_id}")
async def delete_source(source_id: str, user: dict = Depends(get_current_user)):
    """删除 RSS 源"""
    db = PostgresStore.get_instance()
    source = db.get_source(source_id)
    if not source:
        raise HTTPException(404, "Source not found")

    db.delete_source(source_id)
    return {"ok": True}
