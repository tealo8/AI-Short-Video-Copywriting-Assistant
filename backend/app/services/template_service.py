# -*- coding: utf-8 -*-
"""模块8：自定义模板系统（脚本模板 / 文案风格模板 / Prompt 模板 CRUD）。"""
from __future__ import annotations

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ParamError, PermissionError_
from app.db.models import CustomTemplate

SCENE_TYPES = ("script", "style", "prompt")


def serialize_tpl(t: CustomTemplate) -> dict[str, Any]:
    return {
        "id": t.id,
        "name": t.name,
        "scene_type": t.scene_type,
        "description": t.description or "",
        "content": t.content,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "",
        "updated_at": t.updated_at.strftime("%Y-%m-%d %H:%M:%S") if t.updated_at else "",
    }


def list_templates(db: Session, user_id: int, *, scene_type: str = "",
                   keyword: str = "", page: int = 1, page_size: int = 12) -> tuple[int, list[dict]]:
    """标准后端分页：返回 (total, records)，场景 + 名称/内容关键词与分页组合查询。"""
    q = db.query(CustomTemplate).filter(CustomTemplate.user_id == user_id)
    if scene_type:
        q = q.filter(CustomTemplate.scene_type == scene_type)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(CustomTemplate.name.like(like), CustomTemplate.description.like(like)))
    total = q.count()
    rows = (
        q.order_by(CustomTemplate.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, [serialize_tpl(t) for t in rows]


def create_template(db: Session, user_id: int, *, name: str, scene_type: str,
                    content: str, description: str = "") -> dict:
    if not name.strip():
        raise ParamError("模板名称不能为空")
    if scene_type not in SCENE_TYPES:
        raise ParamError(f"场景类型非法，可选: {', '.join(SCENE_TYPES)}")
    if len(content.strip()) < 5:
        raise ParamError("模板内容至少 5 字")
    tpl = CustomTemplate(user_id=user_id, name=name.strip(), scene_type=scene_type,
                         content=content.strip(), description=description.strip())
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return serialize_tpl(tpl)


def _get_owned(db: Session, user_id: int, tpl_id: int) -> CustomTemplate:
    t = db.get(CustomTemplate, tpl_id)
    if not t:
        raise NotFoundError("模板不存在")
    if t.user_id != user_id:
        raise PermissionError_("无权操作该模板")
    return t


def update_template(db: Session, user_id: int, tpl_id: int, patch: dict) -> dict:
    t = _get_owned(db, user_id, tpl_id)
    for k in ("name", "scene_type", "content", "description"):
        if k in patch and patch[k] is not None:
            setattr(t, k, patch[k].strip())
    db.commit()
    db.refresh(t)
    return serialize_tpl(t)


def delete_template(db: Session, user_id: int, tpl_id: int) -> None:
    t = _get_owned(db, user_id, tpl_id)
    db.delete(t)
    db.commit()
