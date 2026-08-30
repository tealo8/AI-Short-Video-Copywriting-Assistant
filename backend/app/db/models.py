# -*- coding: utf-8 -*-
"""四张核心表：user / content_record / custom_template / batch_task_log。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

# JSON 列必须使用 Mutable 包装：否则原地变更（如批量任务 items 打进度）不会触发脏检测
JSON_MUT_LIST = MutableList.as_mutable(JSON)
JSON_MUT_DICT = MutableDict.as_mutable(JSON)


def _now() -> datetime:
    return datetime.now()


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)  # PBKDF2 加密存储
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)  # 管理员（首个用户自动授权）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ContentRecord(Base):
    """内容生成记录：脚本 / 标题标签 / 改写 / TTS 统一归档。"""

    __tablename__ = "content_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    # 生成主题（关键词）
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    # 场景类型：script | titles | copywriting | tts
    record_type: Mapped[str] = mapped_column(String(32), index=True, default="script")
    platform: Mapped[str] = mapped_column(String(32), default="douyin")
    style: Mapped[str] = mapped_column(String(64), default="通用")
    duration: Mapped[int] = mapped_column(Integer, default=60)
    # 结构化完整内容（JSON：overview/segments/hook/ending 等，按 record_type 解释）
    content: Mapped[dict] = mapped_column(JSON_MUT_DICT, default=dict)
    titles: Mapped[list] = mapped_column(JSON_MUT_LIST, default=list)
    tags: Mapped[list] = mapped_column(JSON_MUT_LIST, default=list)
    tts_text: Mapped[str] = mapped_column(Text, default="")
    body_text: Mapped[str] = mapped_column(Text, default="")
    source_model: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16), default="success")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)  # 软删除
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class CustomTemplate(Base):
    """自定义模板：脚本模板 / 文案风格模板 / Prompt 模板。"""

    __tablename__ = "custom_template"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 场景：script | style | prompt
    scene_type: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str] = mapped_column(String(512), default="")
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 模板正文 / Prompt
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class BatchTaskLog(Base):
    """批量任务日志：进度、成败统计、失败详情全量落库，可溯源。"""

    __tablename__ = "batch_task_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="批量生成任务")
    total: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)  # 任务耗时（秒）
    # 结构化记录：{platform, style, duration, source_model} 统一生成参数
    meta: Mapped[dict] = mapped_column(JSON_MUT_DICT, default=dict)
    # [{index, topic, status, message, result_id}] 失败/详情日志
    items: Mapped[list] = mapped_column(JSON_MUT_LIST, default=list)
    error_detail: Mapped[dict] = mapped_column(JSON_MUT_DICT, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
