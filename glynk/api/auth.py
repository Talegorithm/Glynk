"""
Token 验证中间件

所有接口（除注册/登录外）需要 Authorization: Bearer <token>。
"""
from fastapi import Request, HTTPException, Depends

from glynk.storage.postgres import PostgresStore


async def get_current_user(request: Request) -> dict:
    """从 token 获取用户信息"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "Empty token")

    db = PostgresStore.get_instance()
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")

    return user


async def get_optional_user(request: Request) -> dict | None:
    """可选鉴权（未登录返回 None）"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.removeprefix("Bearer ").strip()
    if not token:
        return None

    db = PostgresStore.get_instance()
    return db.get_user_by_token(token)
