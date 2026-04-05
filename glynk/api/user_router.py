"""
用户管理 API

POST /users/verify-email   发送验证码
POST /users                注册
POST /users/login-email    邮箱验证码登录
GET  /users/me             当前用户信息
"""
import re
import secrets
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from glynk.api.auth import get_current_user
from glynk.storage.postgres import PostgresStore

router = APIRouter(prefix="/users", tags=["users"])

# 简单内存验证码存储（生产环境应用 Redis）
_verification_codes: dict[str, str] = {}


class VerifyEmailRequest(BaseModel):
    email: str


class RegisterRequest(BaseModel):
    uid: str
    email: str
    code: str
    name: str = ""


class LoginEmailRequest(BaseModel):
    email: str
    code: str


def _validate_uid(uid: str) -> bool:
    return bool(re.match(r'^[a-z0-9\-]{3,20}$', uid))


def _generate_token() -> str:
    return f"glk_{secrets.token_hex(24)}"


@router.post("/verify-email")
async def verify_email(req: VerifyEmailRequest):
    """发送邮箱验证码"""
    code = f"{secrets.randbelow(900000) + 100000}"
    _verification_codes[req.email] = code

    # TODO: 实际发送邮件
    # 开发阶段直接返回验证码
    return {"message": "验证码已发送", "code": code}


@router.post("")
async def register(req: RegisterRequest):
    """注册新用户"""
    if not _validate_uid(req.uid):
        raise HTTPException(400, "uid 格式无效（小写字母+数字+连字符，3-20字符）")

    # 验证码校验
    expected = _verification_codes.get(req.email)
    if not expected or expected != req.code:
        raise HTTPException(400, "验证码无效或已过期")

    db = PostgresStore.get_instance()

    # 检查 uid 是否已存在
    if db.get_user_by_uid(req.uid):
        raise HTTPException(409, "uid 已被占用")

    # 检查 email 是否已注册
    if db.get_user_by_email(req.email):
        raise HTTPException(409, "该邮箱已注册")

    token = _generate_token()
    db.create_user(req.uid, token, req.email, req.name)

    # 清除验证码
    _verification_codes.pop(req.email, None)

    return {"uid": req.uid, "token": token}


@router.post("/login-email")
async def login_email(req: LoginEmailRequest):
    """邮箱验证码登录"""
    expected = _verification_codes.get(req.email)
    if not expected or expected != req.code:
        raise HTTPException(400, "验证码无效或已过期")

    db = PostgresStore.get_instance()
    user = db.get_user_by_email(req.email)
    if not user:
        raise HTTPException(404, "该邮箱未注册")

    _verification_codes.pop(req.email, None)

    return {"uid": user["uid"], "token": user["token"]}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "uid": user["uid"],
        "name": user.get("name", ""),
        "email": user["email"],
        "created_at": user.get("created_at"),
    }
