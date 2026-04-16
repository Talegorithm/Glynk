"""
Auth API

POST /auth/register    注册 -> Entity + auth record
GET  /auth/me          当前用户 Entity
"""
import secrets
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from glynk.api.auth import get_current_user
from glynk.storage.postgres import PostgresStore

router = APIRouter(prefix="/auth", tags=["auth"])


def _generate_entity_id() -> str:
    return f"ent-{uuid4().hex[:12]}"


def _generate_token() -> str:
    return f"glk_{secrets.token_hex(24)}"


class RegisterRequest(BaseModel):
    display_name: str = ""
    email: str = ""


@router.post("/register")
async def register(req: RegisterRequest):
    """注册：创建 Entity + auth record"""
    db = PostgresStore.get_instance()

    if req.email and db.get_auth_by_email(req.email):
        raise HTTPException(409, "该邮箱已注册")

    entity_id = _generate_entity_id()
    while db.get_entity(entity_id):
        entity_id = _generate_entity_id()

    db.create_entity(
        entity_id=entity_id,
        kind='human',
        state='active',
        display_name=req.display_name or entity_id,
    )

    token = _generate_token()
    email = req.email or f"{entity_id}@placeholder.glynk"
    db.create_auth(entity_id, token, email)

    return {"entity_id": entity_id, "token": token}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "entity_id": user["entity_id"],
        "display_name": user.get("display_name", ""),
        "email": user.get("email", ""),
        "kind": user.get("kind", "human"),
        "state": user.get("state", "active"),
        "created_at": user.get("created_at"),
    }
