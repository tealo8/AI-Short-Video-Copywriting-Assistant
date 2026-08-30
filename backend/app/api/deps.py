# -*- coding: utf-8 -*-
"""FastAPI 依赖：鉴权、会话。"""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, PermissionError_
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None:
        raise AuthError("未登录或登录已过期")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", 0))
        if user_id <= 0:
            raise ValueError("无效用户")
    except Exception as exc:  # noqa: BLE001 jwt 异常统一归一
        raise AuthError("登录凭证无效或已过期，请重新登录") from exc
    user = db.get(User, user_id)
    if not user:
        raise AuthError("用户不存在")
    return {"id": user.id, "username": user.username, "is_admin": bool(user.is_admin)}


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """管理员专属接口守卫。"""
    if not user.get("is_admin"):
        raise PermissionError_("需要管理员权限")
    return user
