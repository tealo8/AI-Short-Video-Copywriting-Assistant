# -*- coding: utf-8 -*-
"""模块7：历史记录管理系统（检索 / 二次编辑 / 复用 / 软删除 / 恢复）。"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionError_
from app.db.models import ContentRecord

RECORD_TYPES = ("script", "titles", "copywriting", "tts")


def serialize_record(r: ContentRecord) -> dict[str, Any]:
    return {
        "id": r.id,
        "topic": r.topic,
        "record_type": r.record_type,
        "platform": r.platform,
        "style": r.style,
        "duration": r.duration,
        "content": r.content or {},
        "titles": r.titles or [],
        "tags": r.tags or [],
        "tts_text": r.tts_text or "",
        "body_text": r.body_text or "",
        "source_model": r.source_model,
        "status": r.status,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
        "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else "",
    }


def list_records(
    db: Session, user_id: int, *, keyword: str = "", record_type: str = "",
    platform: str = "", date_from: str = "", date_to: str = "",
    page: int = 1, page_size: int = 12,
) -> tuple[int, list[dict]]:
    """标准后端分页：返回 (total, records)，筛选条件与分页组合查询。"""
    q = db.query(ContentRecord).filter(
        ContentRecord.user_id == user_id, ContentRecord.is_deleted.is_(False)
    )
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(ContentRecord.topic.like(like), ContentRecord.body_text.like(like)))
    if record_type:
        q = q.filter(ContentRecord.record_type == record_type)
    if platform:
        q = q.filter(ContentRecord.platform == platform)
    if date_from:
        try:
            q = q.filter(ContentRecord.created_at >= datetime.strptime(date_from, "%Y-%m-%d"))
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(ContentRecord.created_at <= datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1))
        except ValueError:
            pass
    total = q.count()
    rows = (
        q.order_by(ContentRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, [serialize_record(r) for r in rows]


def get_owned(db: Session, user_id: int, record_id: int) -> ContentRecord:
    r = db.get(ContentRecord, record_id)
    if not r or r.is_deleted:
        raise NotFoundError("记录不存在或已删除")
    if r.user_id != user_id:
        raise PermissionError_("无权访问该记录")
    return r


def update_record(db: Session, user_id: int, record_id: int, patch: dict) -> dict:
    r = get_owned(db, user_id, record_id)
    allowed = {"topic", "style", "duration", "platform"}
    for k, v in patch.items():
        if k in allowed:
            setattr(r, k, v)
    if patch.get("status") in ("success", "reused"):
        r.status = patch["status"]
    db.commit()
    db.refresh(r)
    return serialize_record(r)


def soft_delete(db: Session, user_id: int, record_id: int) -> None:
    r = get_owned(db, user_id, record_id)
    r.is_deleted = True
    db.commit()


def bulk_soft_delete(db: Session, user_id: int, record_ids: list[int]) -> int:
    """批量软删除，返回实际删除条数。"""
    if not record_ids:
        return 0
    rows = (
        db.query(ContentRecord)
        .filter(ContentRecord.id.in_(record_ids), ContentRecord.user_id == user_id,
                ContentRecord.is_deleted.is_(False))
        .all()
    )
    for r in rows:
        r.is_deleted = True
    db.commit()
    return len(rows)


def hard_delete(db: Session, user_id: int, record_id: int) -> None:
    """永久删除（二次确认后调用）。"""
    r = db.get(ContentRecord, record_id)
    if not r or r.user_id != user_id:
        raise NotFoundError("记录不存在")
    db.delete(r)
    db.commit()


def bulk_hard_delete(db: Session, user_id: int, record_ids: list[int]) -> int:
    """批量永久删除（含已软删除的记录）。"""
    if not record_ids:
        return 0
    rows = (
        db.query(ContentRecord)
        .filter(ContentRecord.id.in_(record_ids), ContentRecord.user_id == user_id)
        .all()
    )
    for r in rows:
        db.delete(r)
    db.commit()
    return len(rows)


def records_by_ids(db: Session, user_id: int, record_ids: list[int]) -> list[ContentRecord]:
    if not record_ids:
        return []
    return (
        db.query(ContentRecord)
        .filter(ContentRecord.id.in_(record_ids), ContentRecord.user_id == user_id,
                ContentRecord.is_deleted.is_(False))
        .all()
    )


def restore(db: Session, user_id: int, record_id: int) -> dict:
    r = db.get(ContentRecord, record_id)
    if not r or r.user_id != user_id or not r.is_deleted:
        raise NotFoundError("记录不存在")
    r.is_deleted = False
    db.commit()
    db.refresh(r)
    return serialize_record(r)
