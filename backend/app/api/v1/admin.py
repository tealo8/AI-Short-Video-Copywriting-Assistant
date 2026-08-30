# -*- coding: utf-8 -*-
"""管理后台接口：用户管理 + 系统日志查看（仅管理员，前端隐藏入口）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.exceptions import NotFoundError, ParamError
from app.core.logging import get_logger
from app.core.response import ok
from app.core.security import hash_password
from app.db.database import get_db
from app.db.models import User

router = APIRouter(prefix="/admin", tags=["管理后台"])
logger = get_logger("admin")


class CreateUserReq(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    is_admin: bool = False


class ResetPasswordReq(BaseModel):
    password: str = Field(min_length=6, max_length=64)


def _dump(u: User) -> dict:
    return {
        "id": u.id, "username": u.username, "is_admin": bool(u.is_admin),
        "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
        "last_login_at": u.last_login_at.strftime("%Y-%m-%d %H:%M:%S") if u.last_login_at else "",
    }


@router.get("/users")
def list_users(admin: dict = Depends(require_admin), db: Session = Depends(get_db),
               page: int = Query(1, ge=1, description="页码（1 起）"),
               page_size: int = Query(20, ge=1, le=100, description="每页条数"),
               filter_keyword: str = Query("", description="用户名关键词"),
               grade: str = Query("", description="角色筛选：admin/normal")):
    q = db.query(User)
    if filter_keyword:
        q = q.filter(User.username.like(f"%{filter_keyword}%"))
    if grade:
        q = q.filter(User.is_admin.is_(grade == "admin"))
    total = q.count()
    users = (
        q.order_by(User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return ok({"total": total, "records": [_dump(u) for u in users]})


@router.post("/users")
def create_user(req: CreateUserReq, admin: dict = Depends(require_admin),
                db: Session = Depends(get_db)):
    username = req.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise ParamError("用户名已存在")
    u = User(username=username, password_hash=hash_password(req.password), is_admin=req.is_admin)
    db.add(u)
    db.commit()
    db.refresh(u)
    logger.info("管理员 %s 创建用户 %s", admin["username"], username)
    return ok(_dump(u), message="用户创建成功")


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: int, req: ResetPasswordReq,
                   admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise NotFoundError("用户不存在")
    u.password_hash = hash_password(req.password)
    db.commit()
    logger.info("管理员 %s 重置了用户 %s 的密码", admin["username"], u.username)
    return ok(message="密码已重置")


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(require_admin), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise NotFoundError("用户不存在")
    if u.id == admin["id"]:
        raise ParamError("不能删除当前登录账号")
    if u.is_admin and db.query(User).filter(User.is_admin.is_(True)).count() <= 1:
        raise ParamError("系统至少保留一名管理员")
    db.delete(u)
    db.commit()
    logger.info("管理员 %s 删除用户 %s", admin["username"], u.username)
    return ok(message="用户已删除")


@router.get("/logs")
def view_logs(admin: dict = Depends(require_admin),
              page: int = Query(1, ge=1, description="页码（1 起）"),
              page_size: int = Query(100, ge=10, le=500, description="每页行数"),
              filter_keyword: str = Query("", description="关键词过滤"),
              grade: str = Query("", description="分级筛选：INFO/WARNING/ERROR")):
    """滚动日志的标准分页读取（先取尾部 2000 行再按条件过滤），IDE 级排查体验。"""
    from pathlib import Path

    from app.config import settings

    log_file = Path(settings.LOG_DIR) / "app.log"
    if not log_file.exists():
        return ok({"total": 0, "records": []})

    raw = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    tail = raw[-2000:] if len(raw) > 2000 else raw
    level = grade.upper()
    if level:
        tail = [ln for ln in tail if f"| {level:<7} |" in ln or f" {level} " in ln]
    if filter_keyword:
        tail = [ln for ln in tail if filter_keyword in ln]
    total = len(tail)
    records = tail[(page - 1) * page_size : page * page_size]
    return ok({"total": total, "records": records})
