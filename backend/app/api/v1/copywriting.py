# -*- coding: utf-8 -*-
"""模块3 接口：智能文案编辑器。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.schemas.api_schemas import CopywritingReq
from app.services.copywriting_service import transform_text

router = APIRouter(prefix="/copywriting", tags=["智能文案编辑器"])


@router.post("/transform")
def transform(req: CopywritingReq, user: dict = Depends(get_current_user),
              db: Session = Depends(get_db)):
    result = transform_text(
        db, user["id"],
        text=req.text, action=req.action, style=req.style, custom_style=req.custom_style,
        demo=req.demo,
    )
    return ok(result, message="演示数据已生成" if req.demo else "文案处理完成")
