"""
内容 API

GET  /content/{content_id}           内容详情
GET  /content/{content_id}/read      统一阅读接口
GET  /content/{content_id}/outline   获取AI大纲
PUT  /content/{content_id}/outline   提交AI大纲
GET  /content/{content_id}/progress  阅读进度
PUT  /content/{content_id}/progress  保存阅读进度
POST /reading-sessions               创建阅读会话
PUT  /reading-sessions/{id}/end      结束阅读会话
GET  /contents                       内容列表
"""
import json
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, Annotated

from glynk.api.auth import get_current_user, get_optional_user
from glynk.content.reader import ReaderService
from glynk.content.translation import translate_file_on_disk
from glynk.storage.postgres import PostgresStore
from glynk.config import AppConfig

router = APIRouter(tags=["content"])

_reader: Optional[ReaderService] = None


def set_reader(reader: ReaderService):
    global _reader
    _reader = reader


@router.get("/content/{content_id}")
async def get_content_detail(content_id: str):
    """内容详情（元数据 + TOC）"""
    db = PostgresStore.get_instance()
    content = db.get_content(content_id)
    if not content:
        raise HTTPException(404, "Content not found")

    try:
        toc = json.loads(content.get("toc_json", "[]"))
    except Exception:
        toc = []

    try:
        outline_raw = json.loads(content.get("ai_outline_json", "[]"))
    except Exception:
        outline_raw = []

    # 统一 outline 字段名：agent 存 span_id，前端期望 location
    def normalize_outline(items: list) -> list:
        for item in items:
            if "span_id" in item and "location" not in item:
                item["location"] = item.pop("span_id")
            if item.get("children"):
                normalize_outline(item["children"])
        return items

    outline = normalize_outline(outline_raw)

    return {
        "content_id": content["content_id"],
        "title": content.get("title", ""),
        "author": content.get("author", ""),
        "source_type": content.get("source_type", ""),
        "source_url": content.get("source_url"),
        "file_count": content.get("file_count", 0),
        "total_chars": content.get("total_chars", 0),
        "abstract": content.get("abstract", ""),
        "toc": toc,
        "outline": outline,
        "created_at": content.get("created_at"),
    }


@router.get("/content/{content_id}/file")
async def read_file(
    request: Request,
    content_id: str,
    lang: str = None,
    user: dict = Depends(get_optional_user),
):
    """人类阅读：加载完整文件"""
    if _reader is None:
        raise HTTPException(500, "Reader not initialized")

    from_span = request.query_params.get("from")
    # optionally support explicit file_idx
    file_idx_str = request.query_params.get("file_idx")
    file_idx = int(file_idx_str) if file_idx_str and file_idx_str.isdigit() else None
    
    uid = user["uid"] if user else None

    try:
        response = _reader.read_file(
            content_id=content_id,
            file_idx=file_idx,
            from_span=from_span,
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


class TranslateRequest(BaseModel):
    file_idx: int


@router.post("/content/{content_id}/translate")
async def translate_file_endpoint(content_id: str, req: TranslateRequest,
                                  user: dict = Depends(get_current_user)):
    """翻译指定文件，目标语言取用户偏好"""
    config = AppConfig.from_env()
    db = PostgresStore.get_instance()
    # 读取用户偏好语言
    user_row = db.get_user_by_uid(user["uid"])
    target_lang = user_row.get("preferred_lang") if user_row else None
    try:
        lang_code, status = translate_file_on_disk(
            config.storage.html_root, content_id, req.file_idx, target_lang
        )
        return {"lang": lang_code, "status": status}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Translation failed: {e}")


@router.get("/content/{content_id}/chunk")
async def read_chunk(
    request: Request,
    content_id: str,
    size: int = Query(..., gt=0),
    user: dict = Depends(get_optional_user),
):
    """AI阅读：获取精简HTML切片"""
    if _reader is None:
        raise HTTPException(500, "Reader not initialized")

    from_span = request.query_params.get("from")
    uid = user["uid"] if user else None

    try:
        response = _reader.read_chunk(
            content_id=content_id,
            from_span=from_span,
            size=size,
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

    # 统一字段名
    def normalize(items: list) -> list:
        for item in items:
            if "span_id" in item and "location" not in item:
                item["location"] = item.pop("span_id")
            if item.get("children"):
                normalize(item["children"])
        return items

    return {"outline": normalize(outline)}


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
    total = db.count_contents()
    return {"contents": contents, "total": total}


# --- Reading Progress ---

class ProgressRequest(BaseModel):
    span_id: str


@router.get("/content/{content_id}/progress")
async def get_progress(content_id: str, user: dict = Depends(get_current_user)):
    """获取阅读进度"""
    db = PostgresStore.get_instance()
    progress = db.get_reading_progress(user["uid"], content_id)
    if not progress:
        raise HTTPException(404, "No reading progress")
    return progress


@router.put("/content/{content_id}/progress")
async def save_progress(content_id: str, req: ProgressRequest,
                        user: dict = Depends(get_current_user)):
    """保存阅读进度"""
    db = PostgresStore.get_instance()
    db.upsert_reading_progress(user["uid"], content_id, req.span_id)
    return {"ok": True}


# --- Reading Sessions ---

class SessionStartRequest(BaseModel):
    content_id: str
    source: str = "manual"


class SessionEndRequest(BaseModel):
    duration_seconds: int | None = None


@router.post("/reading-sessions", status_code=201)
async def start_session(req: SessionStartRequest,
                        user: dict = Depends(get_current_user)):
    """开始阅读会话"""
    db = PostgresStore.get_instance()
    session_id = f"rs-{uuid4().hex[:12]}"
    db.create_reading_session(session_id, user["uid"], req.content_id, req.source)
    return {"session_id": session_id}


@router.api_route("/reading-sessions/{session_id}/end", methods=["PUT", "POST"])
async def end_session(session_id: str, req: SessionEndRequest,
                      user: dict = Depends(get_optional_user)):
    """结束阅读会话"""
    db = PostgresStore.get_instance()
    db.end_reading_session(session_id, req.duration_seconds)
    return {"ok": True}
