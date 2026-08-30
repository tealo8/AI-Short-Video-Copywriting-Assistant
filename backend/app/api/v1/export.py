# -*- coding: utf-8 -*-
"""模块6 接口：Word 标准化导出。"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.services import export_service
from app.services.history_service import get_owned

router = APIRouter(prefix="/export", tags=["文档导出"])


def _stream(buf, filename: str) -> StreamingResponse:
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}.docx"},
    )


@router.post("/script")
def export_script_bundle(payload: dict, user: dict = Depends(get_current_user)):
    """前端把生成套装原样回传，直接出 Word（无需落库即可导出）。"""
    buf = export_service.build_script_docx(payload)
    return _stream(buf, f"短视频脚本_{payload.get('topic', 'untitled')[:24]}")


@router.get("/record/{record_id}")
def export_record(record_id: int, user: dict = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    r = get_owned(db, user["id"], record_id)
    buf = export_service.record_to_docx(r)
    if buf is None:
        return ok(message="该记录类型暂不支持导出")
    return _stream(buf, f"{r.record_type}_{r.topic[:24]}")
