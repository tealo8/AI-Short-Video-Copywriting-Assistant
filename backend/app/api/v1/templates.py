# -*- coding: utf-8 -*-
"""模块8 接口：自定义模板 CRUD。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.schemas.api_schemas import TemplateCreateReq, TemplateUpdateReq
from app.services import template_service

router = APIRouter(prefix="/templates", tags=["自定义模板"])


@router.get("")
def list_templates(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码（1 起）"),
    page_size: int = Query(12, ge=1, le=100, description="每页条数"),
    filter_keyword: str = Query("", description="名称/描述关键词"),
    grade: str = Query("", description="分级筛选：script/style/prompt"),
    scene_type: str = Query("", description="场景筛选（兼容别名，等价 grade）"),
):
    scene = grade or scene_type
    total, records = template_service.list_templates(
        db, user["id"], scene_type=scene, keyword=filter_keyword,
        page=page, page_size=page_size,
    )
    return ok({"total": total, "records": records})


@router.post("")
def create_template(req: TemplateCreateReq, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return ok(template_service.create_template(
        db, user["id"], name=req.name, scene_type=req.scene_type,
        content=req.content, description=req.description), message="模板已创建")


@router.put("/{tpl_id}")
def update_template(tpl_id: int, req: TemplateUpdateReq,
                    user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    patch = {k: v for k, v in req.model_dump().items() if v is not None}
    return ok(template_service.update_template(db, user["id"], tpl_id, patch),
              message="模板已更新")


@router.delete("/{tpl_id}")
def delete_template(tpl_id: int, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    template_service.delete_template(db, user["id"], tpl_id)
    return ok(message="模板已删除")
