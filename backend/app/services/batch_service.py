# -*- coding: utf-8 -*-
"""模块4：批量内容生成（项目核心亮点）。

架构：FastAPI 接口线程池 + ThreadPoolExecutor 后台执行 + DB 进度落库。
- 不阻塞请求：接口秒回 task_id，进度由前端轮询；
- 失败不中断：单条失败记录到 items 日志，继续处理后续条目；
- 可取消：任务级 cancel 标志，条目间隙检查；
- 可溯源：batch_task_log 全量落库（总数/成功/失败/耗时/失败详情）。
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.config import settings
from app.core.exceptions import NotFoundError, ParamError
from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.db.models import BatchTaskLog, ContentRecord
from app.services.script_service import generate_script

logger = get_logger("service.batch")

_executor = ThreadPoolExecutor(max_workers=settings.BATCH_MAX_WORKERS, thread_name_prefix="batch")
_cancel_flags: dict[int, threading.Event] = {}
_lock = threading.Lock()


def create_task(
    db: Session,
    user_id: int,
    *,
    name: str,
    topics: list[str],
    platform: str = "douyin",
    duration: int = 60,
    style: str = "通用",
) -> int:
    topics = [t.strip() for t in topics if t and t.strip()]
    if not topics:
        raise ParamError("未解析到任何主题")
    if len(topics) > settings.BATCH_ITEM_LIMIT:
        raise ParamError(f"单次最多 {settings.BATCH_ITEM_LIMIT} 条（当前 {len(topics)} 条），请分批提交")

    task = BatchTaskLog(
        user_id=user_id,
        name=name or f"批量生成 {len(topics)} 条",
        total=len(topics),
        status="pending",
        meta={"platform": platform, "duration": duration, "style": style},
        items=[{"index": i + 1, "topic": t, "status": "pending"} for i, t in enumerate(topics)],
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id

    _cancel_flags[task_id] = threading.Event()
    _executor.submit(_run_task, task_id)
    logger.info("批量任务已创建 id=%s total=%s", task_id, len(topics))
    return task_id


def cancel_task(task_id: int) -> bool:
    with _lock:
        flag = _cancel_flags.get(task_id)
    if not flag:
        return False
    flag.set()
    return True


def _run_task(task_id: int) -> None:
    t0 = time.time()
    session: Session = SessionLocal()
    try:
        task = session.get(BatchTaskLog, task_id)
        flag = _cancel_flags[task_id]
        task.status = "running"
        session.commit()

        meta = task.meta or {}
        for item in task.items or []:
            if flag.is_set():
                item["status"] = "cancelled"
                continue
            try:
                result = generate_script(
                    session, task.user_id,
                    topic=item["topic"],
                    platform=meta.get("platform", "douyin"),
                    duration=int(meta.get("duration", 60)),
                    style=meta.get("style", "通用"),
                    save_record=True,
                )
                item["status"] = "success"
                item["result_id"] = result["record_id"]
                item["source_model"] = result["source_model"]
                task.success = sum(1 for i in task.items if i.get("status") == "success")
            except Exception as exc:  # noqa: BLE001 单条失败不阻断整批
                logger.warning("批量条目失败 task=%s topic=%s: %s", task_id, item["topic"], exc)
                item["status"] = "failed"
                item["error"] = str(exc)[:300]
                task.failed = sum(1 for i in task.items if i.get("status") == "failed")
            flag_modified(task, "items")  # 嵌套 dict 原地变更需显式标记
            session.commit()  # 每条落盘，前端可实时看到进度

        task.duration = round(time.time() - t0, 1)
        task.finished_at = datetime.now()
        if any(i.get("status") == "cancelled" for i in task.items):
            task.status = "cancelled"
        elif task.failed and task.success:
            task.status = "partial"      # 部分失败：成功+失败混合
        elif task.failed == task.total:
            task.status = "failed"
        else:
            task.status = "completed"
        task.error_detail = {
            f"#{i['index']} {i['topic']}": i.get("error", "")
            for i in task.items if i.get("status") == "failed"
        }
        session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("批量任务运行异常 task=%s", task_id)
        session.rollback()
        task = session.get(BatchTaskLog, task_id)
        if task:
            task.status = "failed"
            task.error_detail = {"fatal": str(exc)[:500]}
            session.commit()
    finally:
        session.close()
        _cancel_flags.pop(task_id, None)
        logger.info("批量任务结束 id=%s", task_id)


def get_task_snapshot(db: Session, task: BatchTaskLog) -> dict:
    items = task.items or []
    progress = round((task.success + task.failed) / task.total * 100, 1) if task.total else 0
    return {
        "id": task.id,
        "name": task.name,
        "total": task.total,
        "success": task.success,
        "failed": task.failed,
        "status": task.status,
        "progress": progress,
        "duration": task.duration,
        "meta": task.meta,
        "error_detail": task.error_detail,
        "created_at": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "",
        "finished_at": task.finished_at.strftime("%Y-%m-%d %H:%M:%S") if task.finished_at else "",
        "items": items,
    }


def list_task_logs(db: Session, user_id: int, *, page: int = 1, page_size: int = 10,
                   keyword: str = "", status: str = "") -> tuple[int, list[dict]]:
    """标准后端分页：返回 (total, records)，名称关键词 + 状态筛选与分页组合。"""
    q = db.query(BatchTaskLog).filter(BatchTaskLog.user_id == user_id)
    if keyword:
        q = q.filter(BatchTaskLog.name.like(f"%{keyword}%"))
    if status:
        q = q.filter(BatchTaskLog.status == status)
    total = q.count()
    rows = (
        q.order_by(BatchTaskLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, [get_task_snapshot(db, t) for t in rows]


def batch_items_to_records(db: Session, user_id: int, task_id: int) -> list[ContentRecord]:
    task = db.get(BatchTaskLog, task_id)
    if not task:
        return []
    ids = [i["result_id"] for i in (task.items or []) if i.get("result_id")]
    return (
        db.query(ContentRecord)
        .filter(ContentRecord.id.in_(ids), ContentRecord.user_id == user_id)
        .all()
        if ids else []
    )


def retry_failed_items(db: Session, user_id: int, task_id: int) -> int:
    """重试失败条目：失败项重置为 pending，重新提交后台执行。返回失败条目数。"""
    task = db.get(BatchTaskLog, task_id)
    if not task or task.user_id != user_id:
        raise NotFoundError("任务不存在")
    failed_items = [i for i in (task.items or []) if i.get("status") == "failed"]
    if not failed_items:
        raise ParamError("没有失败条目需要重试")
    for item in failed_items:
        item["status"] = "pending"
        item.pop("error", None)
        item.pop("result_id", None)
    # 清空统计并重算
    task.success = sum(1 for i in task.items if i.get("status") == "success")
    task.failed = sum(1 for i in task.items if i.get("status") == "failed")
    task.status = "pending"
    task.error_detail = {}
    flag_modified(task, "items")
    db.commit()

    _cancel_flags[task_id] = threading.Event()
    _executor.submit(_run_task, task_id)
    logger.info("批量任务重试提交 task=%s failed=%s", task_id, len(failed_items))
    return len(failed_items)
