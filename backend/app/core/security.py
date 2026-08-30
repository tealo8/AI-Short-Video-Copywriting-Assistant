# -*- coding: utf-8 -*-
"""安全组件：PBKDF2 口令散列 + JWT 无状态鉴权。

- 口令存储：PBKDF2-HMAC-SHA256 / 20 万次迭代 / 16 字节随机盐（OWASP 推荐），
  无第三方依赖，规避 passlib 停止维护、bcrypt 轮子兼容等隐患。
- 鉴权：PyJWT HS256，载荷含 uid / username / exp。
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

_ITERATIONS = 200_000


# ---------------------- 口令散列 ----------------------
def hash_password(raw: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(raw: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        salt = bytes.fromhex(salt_hex)
        expect = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expect)
    except Exception:
        return False


# ---------------------- JWT ----------------------
def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """解析失败统一抛 jwt.PyJWTError，由上层转换为 AuthError。"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
