"""
用户管理 API

POST /users            注册（一键，uid 自动生成）
GET  /users/me         当前用户信息
"""
import secrets
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from glynk.api.auth import get_current_user
from glynk.storage.postgres import PostgresStore

router = APIRouter(prefix="/users", tags=["users"])


def _generate_uid() -> str:
    return f"u-{secrets.token_hex(4)}"


def _generate_token() -> str:
    return f"glk_{secrets.token_hex(24)}"


class RegisterRequest(BaseModel):
    uid: str = ""      # 选填，不填自动生成
    email: str = ""    # 选填


@router.post("")
async def register(req: RegisterRequest):
    """注册：拿 token"""
    db = PostgresStore.get_instance()

    uid = req.uid.strip().lower() if req.uid else _generate_uid()

    if req.uid and db.get_user_by_uid(uid):
        raise HTTPException(409, "uid 已被占用")

    # 自动生成的 uid 冲突极低，但保险起见
    while db.get_user_by_uid(uid):
        uid = _generate_uid()

    if req.email and db.get_user_by_email(req.email):
        raise HTTPException(409, "该邮箱已注册")

    token = _generate_token()
    email = req.email or f"{uid}@placeholder.glynk"
    db.create_user(uid, token, email)

    return {"uid": uid, "token": token}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "uid": user["uid"],
        "email": user.get("email", ""),
        "created_at": user.get("created_at"),
    }
