"""
Publication API —— "发布一份可阅读 / 可被精细标注的内容"

  POST /publications                导入（URL 或路径）
  POST /publications/upload         上传文件导入
  POST /publications/media/init     媒体摄入：签发 OSS 上传 URL
  POST /publications/media/finalize 媒体摄入：转写并落地
"""
import re
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user
from glynk.ingestion.pipeline import (
    IngestionPipeline,
    ContentAlreadyExistsError,
    media_oss_key,
)

router = APIRouter(tags=["publications"])

_pipeline: Optional[IngestionPipeline] = None

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_FILENAME_BAD = re.compile(r"[/\\]")


def set_pipeline(pipeline: IngestionPipeline):
    global _pipeline
    _pipeline = pipeline


class PublicationRequest(BaseModel):
    source: str


@router.post("/publications")
async def create_publication_from_url(
    req: PublicationRequest, user: dict = Depends(get_current_user)
):
    if _pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")

    try:
        result = await _pipeline.ingest(
            source=req.source,
            entity_id=user["entity_id"],
        )
        return {
            "content_id": result.unit_id,
            "title": result.title,
            "author": result.author,
            "source_type": result.source_type,
            "file_count": result.file_count,
            "total_chars": result.total_chars,
            "toc": result.toc,
        }
    except ContentAlreadyExistsError as e:
        u = e.unit
        meta = u.get("metadata") or {} if isinstance(u, dict) else {}
        return {
            "content_id": u.get("id", ""),
            "title": meta.get("title", ""),
            "author": "",
            "source_type": meta.get("source_type", ""),
            "file_count": (u.get("body") or {}).get("file_count", 0),
            "total_chars": meta.get("total_chars", 0),
            "toc": [],
            "existing": True,
        }
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")


class MediaInitRequest(BaseModel):
    filename: str
    file_hash: str
    media_type: str
    title: str
    source_url: Optional[str] = None
    author: Optional[str] = None


class MediaInitResponse(BaseModel):
    unit_id: str
    upload_url: Optional[str] = None
    existing: bool = False


class MediaFinalizeRequest(BaseModel):
    unit_id: str
    filename: str
    media_type: str
    title: str
    file_hash: str
    source_url: Optional[str] = None
    author: Optional[str] = None


def _validate_media_request(filename: str, file_hash: str, media_type: str) -> None:
    if not filename or _FILENAME_BAD.search(filename):
        raise HTTPException(400, "Invalid filename (no path separators allowed)")
    if not _SHA256_RE.match(file_hash.lower()):
        raise HTTPException(400, "file_hash must be sha256 hex (64 lowercase chars)")
    if media_type not in ("audio", "video"):
        raise HTTPException(400, "media_type must be 'audio' or 'video'")


@router.post("/publications/media/init", response_model=MediaInitResponse)
async def create_publication_media_init(
    req: MediaInitRequest, user: dict = Depends(get_current_user)
):
    if _pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    _validate_media_request(req.filename, req.file_hash, req.media_type)

    if not _pipeline.config.oss.enabled:
        raise HTTPException(503, "OSS not configured on server")

    unit_id = req.file_hash.lower()[:16]
    if _pipeline.db.get_unit(unit_id):
        return MediaInitResponse(unit_id=unit_id, upload_url=None, existing=True)

    key = media_oss_key(unit_id, req.filename)
    upload_url = _pipeline.oss_client.presigned_put(key, expires_seconds=1800)
    return MediaInitResponse(unit_id=unit_id, upload_url=upload_url, existing=False)


@router.post("/publications/media/finalize")
async def create_publication_media_finalize(
    req: MediaFinalizeRequest, user: dict = Depends(get_current_user)
):
    if _pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")
    _validate_media_request(req.filename, req.file_hash, req.media_type)

    if req.unit_id != req.file_hash.lower()[:16]:
        raise HTTPException(400, "unit_id must equal file_hash[:16]")

    try:
        result = await _pipeline.ingest_media(
            unit_id=req.unit_id,
            filename=req.filename,
            media_type=req.media_type,
            title=req.title,
            entity_id=user["entity_id"],
            author=req.author or "",
            source_url=req.source_url,
            file_hash=req.file_hash.lower(),
        )
        return {
            "content_id": result.unit_id,
            "title": result.title,
            "author": result.author,
            "source_type": result.source_type,
            "file_count": result.file_count,
            "total_chars": result.total_chars,
            "toc": result.toc,
        }
    except ContentAlreadyExistsError as e:
        u = e.unit
        meta = u.get("metadata") or {} if isinstance(u, dict) else {}
        return {
            "content_id": u.get("id", ""),
            "title": meta.get("title", ""),
            "author": "",
            "source_type": meta.get("source_type", ""),
            "file_count": (u.get("body") or {}).get("file_count", 0),
            "total_chars": meta.get("total_chars", 0),
            "toc": [],
            "existing": True,
        }
    except Exception as e:
        raise HTTPException(500, f"Media ingestion failed: {e}")


@router.post("/publications/upload")
async def create_publication_from_upload(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    if _pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")

    suffix = Path(file.filename).suffix if file.filename else '.html'
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp.close()

    try:
        result = await _pipeline.ingest(
            source=Path(tmp.name),
            entity_id=user["entity_id"],
        )
        return {
            "content_id": result.unit_id,
            "title": result.title,
            "author": result.author,
            "source_type": result.source_type,
            "file_count": result.file_count,
            "total_chars": result.total_chars,
            "toc": result.toc,
        }
    except ContentAlreadyExistsError as e:
        u = e.unit
        meta = u.get("metadata") or {} if isinstance(u, dict) else {}
        return {
            "content_id": u.get("id", ""),
            "title": meta.get("title", ""),
            "author": "",
            "source_type": meta.get("source_type", ""),
            "file_count": (u.get("body") or {}).get("file_count", 0),
            "total_chars": meta.get("total_chars", 0),
            "toc": [],
            "existing": True,
        }
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")
