# -*- coding: utf-8 -*-
"""可选：Celery 分布式任务（预留扩展，默认不加载）。

默认生产路径为进程内 ThreadPoolExecutor（backend/app/services/batch_service.py），
本模块面向"批量量大到单机不够用"的横向扩展场景，无需改动业务代码即可切换：

1. pip install celery redis（写入 requirements 的注释版等效）
2. 启动 worker：celery -A app.tasks.celery_app worker -l info
3. 将 batch_service.create_task 中的 _executor.submit(...) 替换为
   generate_script_task.delay(...) 即可（任务签名见 tasks.py）
"""
from __future__ import annotations

import os

from celery import Celery

CELERY_BROKER = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "ai_content_platform",
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND,
    include=["app.tasks.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_acks_late=True,            # worker 崩溃后任务不丢失（至少一次语义）
    task_time_limit=900,            # 单任务硬超时 15 分钟
    worker_prefetch_multiplier=1,   # 按条分发，避免长尾阻塞
)
