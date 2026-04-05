"""
内容 API

GET  /content/{content_id}/read      统一阅读接口
GET  /content/{content_id}/outline   获取AI大纲
PUT  /content/{content_id}/outline   提交AI大纲
GET  /contents                       内容列表
"""
import json
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, Annotated

from glynk.api.auth import get_current_user, get_optional_user
from glynk.content.reader import ReaderService
from glynk.storage.postgres import PostgresStore

router = APIRouter(tags=["content"])

_reader: Optional[ReaderService] = None


def set_reader(reader: ReaderService):
    global _reader
    _reader = reader


@router.get("/content/{content_id}/read")
async def read_content(
    request: Request,
    content_id: str,
    view: str = Query("human", pattern="^(ai|human)$"),
    lang: str = None,
    size: int = None,
    user: dict = Depends(get_optional_user),
):
    """统一阅读接口"""
    if _reader is None:
        raise HTTPException(500, "Reader not initialized")

    # 'from' is a Python keyword, use Request to get it
    from_span = request.query_params.get("from")
    uid = user["uid"] if user else None

    try:
        response = _reader.read(
            content_id=content_id,
            from_span=from_span,
            size=size,
            view=view,
            lang=lang,
            uid=uid,
        )
        return {
            "content": response.content,
            "from": response.from_span,
            "to": response.to_span,
            "char_count": response.char_count,
            "has_more": response.has_more,
            "next_from": response.next_from,
            "translation_status": response.translation_status,
            "annotations": response.annotations,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/content/{content_id}/outline")
async def get_outline(content_id: str):
    """获取AI大纲"""
    db = PostgresStore.get_instance()
    content = db.get_content(content_id)
    if not content:
        raise HTTPException(404, "Content not found")

    try:
        outline = json.loads(content.get("ai_outline_json", "[]"))
    except Exception:
        outline = []

    return {"outline": outline}


class OutlineRequest(BaseModel):
    outline: list


@router.put("/content/{content_id}/outline")
async def update_outline(content_id: str, req: OutlineRequest,
                         user: dict = Depends(get_current_user)):
    """提交AI大纲"""
    db = PostgresStore.get_instance()
    content = db.get_content(content_id)
    if not content:
        raise HTTPException(404, "Content not found")

    db.update_content_outline(content_id, json.dumps(req.outline, ensure_ascii=False))
    return {"ok": True}


@router.get("/contents")
async def list_contents(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """内容列表"""
    db = PostgresStore.get_instance()
    contents = db.list_contents(limit=limit, offset=offset)
    return {"contents": contents}
