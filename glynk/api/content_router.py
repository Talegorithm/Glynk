"""
Unit API (replaces content_router)

GET  /units/{id}           Unit 详情
GET  /units/{id}/read      阅读（人 / AI）
GET  /units/{id}/outline   AI 大纲
PUT  /units/{id}/outline   提交 AI 大纲
GET  /units                Unit 列表
GET  /units/{id}/progress  阅读进度
PUT  /units/{id}/progress  保存阅读进度
POST /units/search         语义检索
POST /units                创建 authored Unit
POST /reading-sessions     阅读会话
PUT  /reading-sessions/{id}/end
"""
import json
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user, get_optional_user
from glynk.content.reader import ReaderService
from glynk.content.translation import translate_file_on_disk
from glynk.storage.postgres import PostgresStore
from glynk.config import AppConfig
from glynk.models import expand_span_id

router = APIRouter(tags=["units"])

_reader: Optional[ReaderService] = None
_retrieval_engine = None


def set_reader(reader: ReaderService):
    global _reader
    _reader = reader


def set_retrieval_engine(engine):
    global _retrieval_engine
    _retrieval_engine = engine


# --- Unit detail ---

@router.get("/units/{unit_id}")
async def get_unit_detail(unit_id: str):
    """Unit 详情（元数据 + TOC + outline）"""
    db = PostgresStore.get_instance()
    unit = db.get_unit(unit_id)
    if not unit:
        raise HTTPException(404, "Unit not found")

    body = unit.get("body") or {}
    metadata = unit.get("metadata") or {}
    toc = body.get("toc", [])
    outline_raw = metadata.get("ai_outline", [])

    def normalize_outline(items: list) -> list:
        for item in items:
            if "span_id" in item and "location" not in item:
                item["location"] = item.pop("span_id")
            if item.get("children"):
                normalize_outline(item["children"])
        return items

    outline = normalize_outline(outline_raw) if outline_raw else []

    return {
        "content_id": unit["id"],
        "title": metadata.get("title", ""),
        "author": unit.get("author_name", ""),
        "source_type": metadata.get("source_type", ""),
        "source_url": metadata.get("source_url"),
        "file_count": body.get("file_count", 0),
        "total_chars": metadata.get("total_chars", 0),
        "abstract": metadata.get("abstract", ""),
        "language": metadata.get("language"),
        "toc": toc,
        "outline": outline,
        "created_at": unit.get("created_at"),
    }


# --- Read (file / chunk) ---

@router.get("/units/{unit_id}/read")
async def read_unit(
    request: Request,
    unit_id: str,
    size: int = None,
    lang: str = None,
    user: dict = Depends(get_optional_user),
):
    """读取 Unit 内容（不传 size = 整文件，传 size = AI chunk）"""
    if _reader is None:
        raise HTTPException(500, "Reader not initialized")

    from_span = request.query_params.get("from")
    if from_span:
        from_span = expand_span_id(from_span, unit_id)
    file_idx_str = request.query_params.get("file_idx")
    file_idx = int(file_idx_str) if file_idx_str and file_idx_str.isdigit() else None
    entity_id = user["entity_id"] if user else None

    try:
        if size:
            response = _reader.read_chunk(
                content_id=unit_id, from_span=from_span, size=size, entity_id=entity_id,
            )
        else:
            response = _reader.read_file(
                content_id=unit_id, file_idx=file_idx, from_span=from_span,
                lang=lang, entity_id=entity_id,
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


# --- Translate ---

class TranslateRequest(BaseModel):
    file_idx: int


@router.post("/units/{unit_id}/translate")
async def translate_file_endpoint(unit_id: str, req: TranslateRequest,
                                  user: dict = Depends(get_current_user)):
    config = AppConfig.from_env()
    db = PostgresStore.get_instance()
    auth = db.get_auth_by_entity(user["entity_id"])
    target_lang = None  # could store preferred_lang in entity metadata
    try:
        lang_code, status = translate_file_on_disk(
            config.storage.html_root, unit_id, req.file_idx, target_lang, db
        )
        return {"lang": lang_code, "status": status}
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Translation failed: {e}")


# --- Outline ---

@router.get("/units/{unit_id}/outline")
async def get_outline(unit_id: str):
    db = PostgresStore.get_instance()
    unit = db.get_unit(unit_id)
    if not unit:
        raise HTTPException(404, "Unit not found")

    metadata = unit.get("metadata") or {}
    outline = metadata.get("ai_outline", [])

    def normalize(items: list) -> list:
        for item in items:
            if "span_id" in item and "location" not in item:
                item["location"] = item.pop("span_id")
            if item.get("children"):
                normalize(item["children"])
        return items

    return {"outline": normalize(outline) if outline else []}


class OutlineRequest(BaseModel):
    outline: list


@router.put("/units/{unit_id}/outline")
async def update_outline(unit_id: str, req: OutlineRequest,
                         user: dict = Depends(get_current_user)):
    db = PostgresStore.get_instance()
    unit = db.get_unit(unit_id)
    if not unit:
        raise HTTPException(404, "Unit not found")

    db.update_unit_metadata_key(unit_id, "ai_outline", req.outline)
    return {"ok": True}


# --- List Units ---

@router.get("/units")
async def list_units(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    origin: str = None,
    author_id: str = None,
    user: dict = Depends(get_optional_user),
):
    db = PostgresStore.get_instance()
    
    # Map author_id="me" to current user's entity_id
    if author_id == "me":
        if not user:
            raise HTTPException(401, "Authentication required to use author_id=me")
        author_id = user["entity_id"]
        
    units = db.list_units(origin=origin, author_id=author_id, limit=limit, offset=offset)
    total = db.count_units(origin=origin, author_id=author_id)

    # Format for frontend compatibility
    contents = []
    for u in units:
        meta = u.get("metadata") or {}
        body = u.get("body") or {}
        contents.append({
            "content_id": u["id"],
            "title": meta.get("title", ""),
            "author": u.get("author_name", ""),
            "source_type": meta.get("source_type", ""),
            "source_url": meta.get("source_url"),
            "file_count": body.get("file_count", 0),
            "total_chars": meta.get("total_chars", 0),
            "abstract": meta.get("abstract", ""),
            "text": body.get("html", ""), # Add text for authored units
            "created_at": u.get("created_at"),
        })

    return {"contents": contents, "total": total}


# --- Create authored Unit ---

class CreateUnitRequest(BaseModel):
    text: str
    metadata: dict = {}


@router.post("/units", status_code=201)
async def create_unit(req: CreateUnitRequest, user: dict = Depends(get_current_user)):
    """创建 authored Unit（放下想法）。文本足够长时自动生成 embedding。"""
    from glynk.embedding.service import generate_embedding, should_embed

    db = PostgresStore.get_instance()
    unit_id = f"u-{uuid4().hex[:12]}"

    vector = None
    vector_text = None
    if should_embed(req.text, req.metadata):
        cfg = AppConfig.from_env()
        vector = await generate_embedding(req.text, cfg.embedding)
        vector_text = req.text

    db.create_unit(
        unit_id=unit_id,
        author_id=user["entity_id"],
        origin='authored',
        shape='flat',
        body={"html": req.text},
        metadata=req.metadata,
        vector=vector,
        vector_text=vector_text,
    )
    return {"id": unit_id}


# --- Search ---

class SearchRequest(BaseModel):
    text: str
    types: list[str] | None = None
    content_ids: list[str] | None = None
    top_k: int = 10


@router.post("/units/search")
async def search_units(req: SearchRequest, user: dict = Depends(get_optional_user)):
    if _retrieval_engine is None:
        raise HTTPException(500, "Service not initialized")

    from glynk.models import QueryRequest
    query = QueryRequest(
        text=req.text,
        roles=req.types or ["highlight", "hook"],
        unit_ids=req.content_ids,
        entity_id=user["entity_id"] if user else None,
        top_k=req.top_k,
    )
    try:
        response = await _retrieval_engine.query(query)
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return {"query_id": response.query_id, "results": response.results}


# --- Reading Progress ---

class ProgressRequest(BaseModel):
    span_id: str


@router.get("/units/{unit_id}/progress")
async def get_progress(unit_id: str, user: dict = Depends(get_current_user)):
    db = PostgresStore.get_instance()
    progress = db.get_reading_progress(user["entity_id"], unit_id)
    if not progress:
        return None
    return progress


@router.put("/units/{unit_id}/progress")
async def save_progress(unit_id: str, req: ProgressRequest,
                        user: dict = Depends(get_current_user)):
    db = PostgresStore.get_instance()
    db.upsert_reading_progress(user["entity_id"], unit_id, req.span_id)
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
    db = PostgresStore.get_instance()
    session_id = f"rs-{uuid4().hex[:12]}"
    db.create_reading_session(session_id, user["entity_id"], req.content_id, req.source)
    return {"session_id": session_id}


@router.api_route("/reading-sessions/{session_id}/end", methods=["PUT", "POST"])
async def end_session(session_id: str, req: SessionEndRequest,
                      user: dict = Depends(get_optional_user)):
    db = PostgresStore.get_instance()
    db.end_reading_session(session_id, req.duration_seconds)
    return {"ok": True}
