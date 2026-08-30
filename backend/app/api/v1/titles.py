# -*- coding: utf-8 -*-
"""模块2 接口：爆款标题 & 话题标签。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.schemas.api_schemas import TitleGenerateReq
from app.services.title_service import generate_title_set

router = APIRouter(prefix="/titles", tags=["爆款标题&标签"])


@router.post("/generate")
def generate(req: TitleGenerateReq, user: dict = Depends(get_current_user),
             db: Session = Depends(get_db)):
    result = generate_title_set(
        db, user["id"],
        topic=req.topic, platform=req.platform,
        action=req.action, existing_titles=req.existing_titles, demo=req.demo,
    )
    return ok(result, message="演示数据已生成" if req.demo else "标题&标签生成成功")
