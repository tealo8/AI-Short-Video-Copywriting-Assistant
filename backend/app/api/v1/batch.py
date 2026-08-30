# -*- coding: utf-8 -*-
"""模块4 接口：批量内容生成（异步任务 + 进度 + 结果打包下载）。"""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.core.response import ok
from app.db.database import get_db
from app.db.models import BatchTaskLog
from app.schemas.api_schemas import BatchTaskCreateReq
from app.services import batch_service, export_service
from app.utils.file_parser import parse_batch_file

router = APIRouter(prefix="/batch", tags=["批量生成"])


@router.post("/tasks")
def create_task(req: BatchTaskCreateReq, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    if not req.topics:
        return ok({"task_id": None}, message="未提供主题列表")
    task_id = batch_service.create_task(
        db, user["id"], name=req.name, topics=req.topics,
        platform=req.platform, duration=req.duration, style=req.style,
    )
    return ok({"task_id": task_id}, message="批量任务已创建，后台执行中")


@router.post("/tasks/upload")
def create_task_from_file(
    file: UploadFile = File(...),
    name: str = Form(""),
    platform: str = Form("douyin"),
    duration: int = Form(60),
    style: str = Form("通用"),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = file.file.read()
    topics = parse_batch_file(file.filename or "", content)
    task_id = batch_service.create_task(
        db, user["id"], name=name or file.filename, topics=topics,
        platform=platform, duration=duration, style=style,
    )
    return ok({"task_id": task_id, "count": len(topics)}, message=f"已导入 {len(topics)} 条主题")


@router.get("/tasks")
def list_tasks(user: dict = Depends(get_current_user), db: Session = Depends(get_db),
               page: int = Query(1, ge=1, description="页码（1 起）"),
               page_size: int = Query(10, ge=1, le=100, description="每页条数"),
               filter_keyword: str = Query("", description="任务名称关键词"),
               grade: str = Query("", description="状态筛选：pending/running/completed/partial/failed/cancelled")):
    total, records = batch_service.list_task_logs(
        db, user["id"], page=page, page_size=page_size,
        keyword=filter_keyword, status=grade,
    )
    return ok({"total": total, "records": records})


@router.get("/tasks/{task_id}")
def task_detail(task_id: int, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    task = db.get(BatchTaskLog, task_id)
    if not task or task.user_id != user["id"]:
        raise NotFoundError("任务不存在")
    return ok(batch_service.get_task_snapshot(db, task))


@router.post("/tasks/{task_id}/cancel")
def cancel(task_id: int, user: dict = Depends(get_current_user),
           db: Session = Depends(get_db)):
    task = db.get(BatchTaskLog, task_id)
    if not task or task.user_id != user["id"]:
        raise NotFoundError("任务不存在")
    cancelled = batch_service.cancel_task(task_id)
    return ok({"cancelled": cancelled}, message="已请求取消" if cancelled else "任务已结束，无需取消")


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, user: dict = Depends(get_current_user),
                db: Session = Depends(get_db)):
    task = db.get(BatchTaskLog, task_id)
    if not task or task.user_id != user["id"]:
        raise NotFoundError("任务不存在")
    db.delete(task)
    db.commit()
    return ok(message="任务记录已删除")


@router.post("/tasks/{task_id}/retry")
def retry_failed(task_id: int, user: dict = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """重试失败条目：失败项重新排队执行。"""
    retried = batch_service.retry_failed_items(db, user["id"], task_id)
    return ok({"retried": retried}, message=f"{retried} 条失败条目已重新排队")


@router.get("/tasks/{task_id}/download-docx")
def download_docx(task_id: int, user: dict = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """批量结果打包导出全部 Word 文档（zip）。"""
    task = db.get(BatchTaskLog, task_id)
    if not task or task.user_id != user["id"]:
        raise NotFoundError("任务不存在")
    records = batch_service.batch_items_to_records(db, user["id"], task_id)
    if not records:
        raise NotFoundError("该任务暂无生成成功的结果")
    buf = export_service.build_records_zip(records)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_docx_{task_id}.zip"},
    )


@router.get("/template")
def download_template(user: dict = Depends(get_current_user)):
    """批量导入模板文件下载（TXT 示例 + 格式说明）。"""
    content = (
        "# AI 内容工场 · 批量生成主题导入模板\n"
        "# 每行一个主题（以#开头的行会被忽略），保存为 .txt 上传即可\n"
        "AI 短视频脚本入门\n"
        "小红书涨粉技巧\n"
        "电商直播带货话术\n"
        "普通人拍 vlog 的第一步\n"
    )
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=batch_template.txt"},
    )


@router.get("/tasks/{task_id}/download")
def download_results(task_id: int, user: dict = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    task = db.get(BatchTaskLog, task_id)
    if not task or task.user_id != user["id"]:
        raise NotFoundError("任务不存在")
    records = batch_service.batch_items_to_records(db, user["id"], task_id)
    by_id = {r.id: r for r in records}

    wb = Workbook()
    ws = wb.active
    ws.title = "批量生成结果"
    ws.append(["序号", "主题", "状态", "爆款标题(前5)", "配音文本", "正文", "记录ID", "失败原因"])
    for item in task.items or []:
        rec = by_id.get(item.get("result_id"))
        ws.append([
            item.get("index"),
            item.get("topic"),
            item.get("status"),
            "\n".join((rec.titles or [])[:5]) if rec else "",
            (rec.tts_text or "")[:800] if rec else "",
            (rec.body_text or "")[:800] if rec else "",
            item.get("result_id", ""),
            item.get("error", ""),
        ])
    for col, width in zip("ABCDEFGH", (6, 28, 10, 60, 60, 60, 10, 40)):
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"batch_result_{task_id}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
