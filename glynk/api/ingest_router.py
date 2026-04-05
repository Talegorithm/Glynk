"""
摄入 API

POST /ingest   导入内容
"""
import json
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

from glynk.api.auth import get_current_user
from glynk.ingestion.pipeline import IngestionPipeline, ContentAlreadyExistsError

router = APIRouter(tags=["ingest"])

# Will be set during app startup
_pipeline: Optional[IngestionPipeline] = None


def set_pipeline(pipeline: IngestionPipeline):
    global _pipeline
    _pipeline = pipeline


class IngestRequest(BaseModel):
    source: str  # URL 或本地文件路径


@router.post("/ingest")
async def ingest_url(req: IngestRequest, user: dict = Depends(get_current_user)):
    """通过 URL 或路径导入内容"""
    if _pipeline is None:
        raise HTTPException(500, "Pipeline not initialized")

    try:
        result = await _pipeline.ingest(
            source=req.source,
            uid=user["uid"],
        )
        return {
            "content_id": result.content_id,
            "title": result.title,
            "author": result.author,
            "source_type": result.source_type,
            "file_count": result.file_count,
            "total_chars": result.total_chars,
            "toc": result.toc,
        }
    except ContentAlreadyExistsError as e:
        raise HTTPException(409, {
            "error": "content_already_exists",
            "content_id": e.content.get("content_id"),
        })
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")


@router.post("/ingest/upload")
async def ingest_file(file: UploadFile = File(...),
                      user: dict = Depends(get_current_user)):
    """上传文件导入"""
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
            uid=user["uid"],
        )
        return {
            "content_id": result.content_id,
            "title": result.title,
            "author": result.author,
            "source_type": result.source_type,
            "file_count": result.file_count,
            "total_chars": result.total_chars,
            "toc": result.toc,
        }
    except ContentAlreadyExistsError as e:
        raise HTTPException(409, {
            "error": "content_already_exists",
            "content_id": e.content.get("content_id"),
        })
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")
