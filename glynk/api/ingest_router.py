"""
摄入 API

POST /ingest         导入内容（URL 或路径）
POST /ingest/upload  上传文件导入
"""
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user
from glynk.ingestion.pipeline import IngestionPipeline, ContentAlreadyExistsError

router = APIRouter(tags=["ingest"])

_pipeline: Optional[IngestionPipeline] = None


def set_pipeline(pipeline: IngestionPipeline):
    global _pipeline
    _pipeline = pipeline


class IngestRequest(BaseModel):
    source: str


@router.post("/ingest")
async def ingest_url(req: IngestRequest, user: dict = Depends(get_current_user)):
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


@router.post("/ingest/upload")
async def ingest_file(file: UploadFile = File(...),
                      user: dict = Depends(get_current_user)):
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
