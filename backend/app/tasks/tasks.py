# -*- coding: utf-8 -*-
"""可选：Celery 任务定义（与进程内 ThreadPoolExecutor 同构替换）。

generate_script_task   —— 单条脚本生成（含结构化校验/质量修复/落库）
retry_with_backoff     —— 演示任务的指数退避重试封装（供自定义任务复用）
"""
from __future__ import annotations

from app.tasks.celery_app import celery_app


@celery_app.task(name="acp.generate_script", bind=True, max_retries=3, soft_time_limit=600)
def generate_script_task(self, user_id: int, topic: str, platform: str = "douyin",
                         duration: int = 60, style: str = "通用",
                         custom_style: str = "", word_budget_min: int | None = None,
                         word_budget_max: int | None = None) -> dict:
    """独立 Session 执行完整生成链路，失败指数退避重试 3 次。"""
    from app.db.database import SessionLocal
    from app.services.script_service import generate_script

    db = SessionLocal()
    try:
        result = generate_script(
            db, user_id, topic=topic, platform=platform, duration=duration,
            style=style, custom_style=custom_style,
            word_budget_min=word_budget_min, word_budget_max=word_budget_max,
            save_record=True,
        )
        return {"code": 0, "record_id": result["record_id"], "topic": topic}
    except Exception as exc:  # noqa: BLE001 网络抖动/模型超时 → 重试
        raise self.retry(exc=exc, countdown=10 * (self.request.retries + 1))
    finally:
        db.close()


@celery_app.task(name="acp.retry_with_backoff", bind=True, max_retries=5)
def retry_with_backoff(self, fn_name: str, **kwargs) -> dict:
    """通用带退避重试的任务封装：name 为业务函数注册名。"""
    import importlib

    module_name, func_name = fn_name.rsplit(".", 1)
    fn = getattr(importlib.import_module(module_name), func_name)
    try:
        return {"code": 0, "result": fn(**kwargs)}
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=5 * 2 ** self.request.retries)
