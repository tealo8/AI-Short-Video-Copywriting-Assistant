# -*- coding: utf-8 -*-
"""鉴权接口：登录（仅登录，不开放注册）/ 修改密码 / 当前用户。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import AuthError, ParamError
from app.core.response import ok
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User
from app.schemas.api_schemas import LoginReq

router = APIRouter(prefix="/auth", tags=["认证"])


class ChangePasswordReq(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=6, max_length=64)


class RegisterReq(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)


def _user_payload(u: User) -> dict:
    return {"id": u.id, "username": u.username, "is_admin": bool(u.is_admin)}


@router.post("/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    """API 层保留注册能力（内部工具默认通过管理后台开号；界面不做注册入口）。"""
    username = req.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise ParamError("用户名已被占用")
    user = User(username=username, password_hash=hash_password(req.password), is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.username)
    return ok({"token": token, "user": _user_payload(user)}, message="注册成功")


@router.post("/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise AuthError("用户名或密码错误")
    user.last_login_at = datetime.now()
    db.commit()
    token = create_access_token(user.id, user.username)
    return ok({"token": token, "user": _user_payload(user)}, message="登录成功")


@router.post("/change-password")
def change_password(req: ChangePasswordReq, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    db_user = db.get(User, user["id"])
    if not db_user or not verify_password(req.old_password, db_user.password_hash):
        raise AuthError("原密码不正确")
    if req.new_password == req.old_password:
        raise ParamError("新密码不能与原密码相同")
    db_user.password_hash = hash_password(req.new_password)
    db.commit()
    return ok(message="密码修改成功，下次登录请使用新密码")


@router.get("/me")
def me(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.get(User, user["id"])
    return ok(_user_payload(db_user) if db_user else user)
