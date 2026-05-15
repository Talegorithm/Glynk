"""
Auth API

POST /auth/register/request-code  发送注册邮箱验证码
POST /auth/register               邮箱验证后注册 -> Entity + auth record
POST /auth/login                  邮箱密码登录
GET  /auth/me          当前用户 Entity
"""
import base64
import hashlib
import hmac
import os
import re
import secrets
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from glynk.api.auth import get_current_user
from glynk.email.service import EmailDeliveryError, send_auth_code_email
from glynk.storage.postgres import PostgresStore

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_ITERATIONS = 260_000
REGISTER_CODE_PURPOSE = "register"


def _generate_entity_id() -> str:
    return f"ent-{uuid4().hex[:12]}"


def _generate_token() -> str:
    return f"glk_{secrets.token_hex(24)}"


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not normalized or not EMAIL_RE.match(normalized):
        raise HTTPException(400, "邮箱格式不正确")
    return normalized


def _validate_password(password: str) -> str:
    if not password or len(password) < 8:
        raise HTTPException(400, "密码至少需要 8 个字符")
    if len(password) > 128:
        raise HTTPException(400, "密码过长")
    return password


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt_b64}${digest_b64}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algo, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.b64decode(salt_b64.encode("ascii")),
            int(iterations),
        )
        return hmac.compare_digest(
            base64.b64encode(digest).decode("ascii"),
            digest_b64,
        )
    except Exception:
        return False


def _hash_auth_code(email: str, purpose: str, code: str) -> str:
    secret = os.getenv("AUTH_CODE_SECRET", "")
    if not secret:
        raise HTTPException(500, "AUTH_CODE_SECRET 未配置")
    message = f"{email}:{purpose}:{code}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


class RegisterRequest(BaseModel):
    display_name: str = ""
    email: str
    password: str
    code: str


class RegisterCodeRequest(BaseModel):
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register/request-code")
async def request_register_code(req: RegisterCodeRequest):
    """发送注册邮箱验证码。"""
    db = PostgresStore.get_instance()
    email = _normalize_email(req.email)

    if db.get_auth_by_email(email):
        raise HTTPException(409, "该邮箱已注册")

    recent = db.get_recent_email_code(email, REGISTER_CODE_PURPOSE, within_seconds=60)
    if recent:
        raise HTTPException(429, "验证码发送过于频繁，请稍后再试")

    code = _generate_code()
    code_hash = _hash_auth_code(email, REGISTER_CODE_PURPOSE, code)
    db.create_email_code(
        code_id=f"email-code-{uuid4().hex}",
        email=email,
        purpose=REGISTER_CODE_PURPOSE,
        code_hash=code_hash,
        ttl_minutes=10,
    )

    try:
        send_auth_code_email(email, code)
    except EmailDeliveryError as exc:
        raise HTTPException(502, "验证码邮件发送失败") from exc

    return {"ok": True}


@router.post("/register")
async def register(req: RegisterRequest):
    """邮箱验证注册：创建 Entity + auth record。"""
    db = PostgresStore.get_instance()

    email = _normalize_email(req.email)
    password = _validate_password(req.password)
    code = (req.code or "").strip()
    if not re.fullmatch(r"\d{6}", code):
        raise HTTPException(400, "验证码格式不正确")

    if db.get_auth_by_email(email):
        raise HTTPException(409, "该邮箱已注册")

    code_row = db.get_latest_email_code(email, REGISTER_CODE_PURPOSE)
    if not code_row:
        raise HTTPException(400, "验证码无效或已过期")
    if code_row.get("attempts", 0) >= 5:
        raise HTTPException(400, "验证码尝试次数过多，请重新获取")

    db.increment_email_code_attempts(code_row["id"])
    expected_hash = _hash_auth_code(email, REGISTER_CODE_PURPOSE, code)
    if not hmac.compare_digest(expected_hash, code_row["code_hash"]):
        raise HTTPException(400, "验证码错误")

    entity_id = _generate_entity_id()
    while db.get_entity(entity_id):
        entity_id = _generate_entity_id()

    display_name = (req.display_name or "").strip() or email.split("@", 1)[0]
    db.create_entity(
        entity_id=entity_id,
        kind='human',
        state='active',
        display_name=display_name,
    )

    token = _generate_token()
    db.create_auth(
        entity_id=entity_id,
        token=token,
        email=email,
        password_hash=_hash_password(password),
        email_verified=True,
    )
    db.consume_email_code(code_row["id"])

    return {"entity_id": entity_id, "token": token}


@router.post("/login")
async def login(req: LoginRequest):
    """邮箱密码登录，返回现有 API token。"""
    db = PostgresStore.get_instance()
    email = _normalize_email(req.email)
    password = req.password or ""

    user = db.get_auth_by_email(email)
    if not user or not user.get("password_hash"):
        raise HTTPException(401, "邮箱或密码错误")
    if user.get("state") != "active":
        raise HTTPException(403, "账号不可用")
    if not _verify_password(password, user["password_hash"]):
        raise HTTPException(401, "邮箱或密码错误")

    return {"entity_id": user["entity_id"], "token": user["token"]}


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
