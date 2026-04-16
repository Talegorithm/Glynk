"""
Internal file write API — 给 local dev 的 RemoteFileStore 用

PUT    /api/internal/files/{unit_id}/{filename}   写文件（raw body）
DELETE /api/internal/files/{unit_id}              删除整个 unit 目录

鉴权：Bearer token 必须在 GLYNK_WRITE_ALLOWED_TOKENS (env, 逗号分隔) 白名单里。
路径校验：unit_id 形如 sha256[:16]；filename 只允许字母数字/点/下划线/短横。
Body 上限 50MB。
"""
import logging
import os
import re
import shutil

from fastapi import APIRouter, HTTPException, Request

from glynk.config import AppConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["internal"])

_UNIT_ID_RE = re.compile(r"^[a-f0-9]{16}$")
_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_MAX_BODY = 50 * 1024 * 1024  # 50MB


def _allowed_tokens() -> set[str]:
    raw = os.getenv("GLYNK_WRITE_ALLOWED_TOKENS", "")
    return {t.strip() for t in raw.split(",") if t.strip()}


def _check_auth(request: Request) -> None:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization header")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Empty token")

    allowed = _allowed_tokens()
    if not allowed:
        # 服务器没配白名单 → 内部写入端点一律禁用
        raise HTTPException(
            403,
            "Internal file writes disabled (GLYNK_WRITE_ALLOWED_TOKENS not set)",
        )
    if token not in allowed:
        raise HTTPException(403, "Token not allowed for internal writes")


def _validate_unit_id(unit_id: str) -> None:
    if not _UNIT_ID_RE.match(unit_id):
        raise HTTPException(400, f"Invalid unit_id: {unit_id!r}")


def _validate_filename(filename: str) -> None:
    if not _FILENAME_RE.match(filename):
        raise HTTPException(400, f"Invalid filename: {filename!r}")


@router.put("/internal/files/{unit_id}/{filename}")
async def put_file(unit_id: str, filename: str, request: Request):
    _check_auth(request)
    _validate_unit_id(unit_id)
    _validate_filename(filename)

    # 大小预检（若提供了 Content-Length）
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > _MAX_BODY:
        raise HTTPException(413, f"Body exceeds {_MAX_BODY} bytes")

    body = await request.body()
    if len(body) > _MAX_BODY:
        raise HTTPException(413, f"Body exceeds {_MAX_BODY} bytes")

    config = AppConfig.from_env()
    unit_dir = config.storage.html_root / unit_id
    unit_dir.mkdir(parents=True, exist_ok=True)
    target = unit_dir / filename
    target.write_bytes(body)
    logger.info(f"Internal write: {unit_id}/{filename} ({len(body)} bytes)")
    return {"ok": True, "size": len(body)}


@router.delete("/internal/files/{unit_id}")
async def delete_unit_dir(unit_id: str, request: Request):
    _check_auth(request)
    _validate_unit_id(unit_id)

    config = AppConfig.from_env()
    unit_dir = config.storage.html_root / unit_id
    if unit_dir.exists():
        shutil.rmtree(unit_dir, ignore_errors=True)
        logger.info(f"Internal delete: {unit_id}/")
        return {"ok": True, "deleted": True}
    return {"ok": True, "deleted": False}
