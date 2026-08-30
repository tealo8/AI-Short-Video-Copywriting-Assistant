# -*- coding: utf-8 -*-
"""模块1 接口：短视频脚本生成（支持 demo 演示模式与字数范围约束）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.schemas.api_schemas import ScriptGenerateReq
from app.services.prompts.templates import PLATFORM_PROFILES
from app.services.script_service import generate_script

router = APIRouter(prefix="/script", tags=["短视频脚本"])


@router.post("/generate")
def generate(req: ScriptGenerateReq, user: dict = Depends(get_current_user),
             db: Session = Depends(get_db)):
    result = generate_script(
        db, user["id"],
        topic=req.topic, platform=req.platform,
        duration=req.duration, style=req.style, custom_style=req.custom_style,
        word_budget_min=req.word_budget_min, word_budget_max=req.word_budget_max,
        demo=req.demo,
    )
    result["platform_name"] = PLATFORM_PROFILES.get(req.platform, {}).get("label", req.platform)
    return ok(result, message="演示数据已生成" if req.demo else "脚本生成成功")
