# -*- coding: utf-8 -*-
"""模块5 接口：TTS 配音专用文本生成（纯规则引擎，毫秒级）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.schemas.api_schemas import TTSReq
from app.services.tts_service import optimize

router = APIRouter(prefix="/tts", tags=["TTS配音文本"])


@router.post("/optimize")
def optimize_tts(req: TTSReq, user: dict = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    result = optimize(req.text)
    return ok(result, message="配音文稿优化完成")
