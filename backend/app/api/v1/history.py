# -*- coding: utf-8 -*-
"""模块7：历史记录管理（标准后端分页 {total, records}）。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.database import get_db
from app.schemas.api_schemas import RecordUpdateReq
from app.services import export_service, history_service

router = APIRouter(prefix="/history", tags=["历史记录"])


class BulkOpReq(BaseModel):
    ids: list[int]


@router.get("")
def list_records(
    user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码（1 起）"),
    page_size: int = Query(12, ge=1, le=100, description="每页条数"),
    filter_keyword: str = Query("", description="关键词过滤（主题/内容）"),
    grade: str = Query("", description="分级筛选：script/titles/copywriting"),
    platform: str = Query("", description="平台筛选：douyin/xiaohongshu/..."),
    date_from: str = Query("", description="起始日期 YYYY-MM-DD"),
    date_to: str = Query("", description="结束日期 YYYY-MM-DD"),
):
    total, records = history_service.list_records(
        db, user["id"], keyword=filter_keyword, record_type=grade, platform=platform,
        date_from=date_from, date_to=date_to, page=page, page_size=page_size,
    )
    return ok({"total": total, "records": records})


@router.get("/{record_id}")
def record_detail(record_id: int, user: dict = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return ok(history_service.serialize_record(
        history_service.get_owned(db, user["id"], record_id)))


@router.put("/{record_id}")
def update_record(record_id: int, req: RecordUpdateReq,
                  user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    patch = {k: v for k, v in req.model_dump().items() if v is not None}
    return ok(history_service.update_record(db, user["id"], record_id, patch),
              message="记录已更新")


@router.delete("/{record_id}")
def soft_delete(record_id: int, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    history_service.soft_delete(db, user["id"], record_id)
    return ok(message="已移入回收站（可恢复）")


@router.delete("/{record_id}/hard")
def hard_delete(record_id: int, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    history_service.hard_delete(db, user["id"], record_id)
    return ok(message="已永久删除")


@router.post("/{record_id}/restore")
def restore(record_id: int, user: dict = Depends(get_current_user),
            db: Session = Depends(get_db)):
    return ok(history_service.restore(db, user["id"], record_id), message="已恢复")


@router.post("/bulk-delete")
def bulk_delete(req: BulkOpReq, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    n = history_service.bulk_soft_delete(db, user["id"], req.ids)
    return ok({"deleted": n}, message=f"已批量移入回收站 {n} 条")


@router.post("/bulk-purge")
def bulk_purge(req: BulkOpReq, user: dict = Depends(get_current_user),
               db: Session = Depends(get_db)):
    n = history_service.bulk_hard_delete(db, user["id"], req.ids)
    return ok({"deleted": n}, message=f"已永久删除 {n} 条")


@router.post("/bulk-export")
def bulk_export(req: BulkOpReq, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """勾选记录打包导出 Word（zip）。"""
    records = history_service.records_by_ids(db, user["id"], req.ids)
    if not records:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("没有可导出的记录")
    buf = export_service.build_records_zip(records)
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=history_export.zip"},
    )
