# -*- coding: utf-8 -*-
"""API 请求 Schema：入参双重校验（框架层 + 服务层）。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterReq(BaseModel):
    username: str = Field(min_length=2, max_length=32, description="用户名")
    password: str = Field(min_length=6, max_length=64, description="密码")


class LoginReq(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=64)


class ScriptGenerateReq(BaseModel):
    topic: str = Field(min_length=2, max_length=100, description="视频主题")
    platform: str = Field(default="douyin", description="douyin/xiaohongshu/shipinhao/bilibili")
    duration: int = Field(default=60, ge=10, le=300, description="时长（秒）")
    style: str = Field(default="通用", max_length=32, description="内容风格")
    custom_style: str = Field(default="", max_length=256, description="自定义风格要求（覆盖内置风格）")
    word_budget_min: int | None = Field(default=None, ge=20, le=800, description="口播台词字数下限")
    word_budget_max: int | None = Field(default=None, ge=20, le=1000, description="口播台词字数上限")
    demo: bool = Field(default=False, description="演示模式：输出预置示例数据，不调用大模型")


class TitleGenerateReq(BaseModel):
    topic: str = Field(min_length=2, max_length=100)
    platform: str = Field(default="douyin")
    action: str = Field(default="generate", description="generate=生成 / polish=二次润色")
    existing_titles: list[str] = Field(default_factory=list, max_length=20)
    demo: bool = Field(default=False, description="演示模式")


class CopywritingReq(BaseModel):
    text: str = Field(min_length=10, max_length=5000, description="原文")
    action: str = Field(default="rewrite", description="rewrite/expand/condense/style_transfer/polish/proofread/dedupe")
    style: str = Field(default="通用", max_length=32)
    custom_style: str = Field(default="", max_length=256)
    demo: bool = Field(default=False, description="演示模式")


class TTSReq(BaseModel):
    text: str = Field(min_length=1, max_length=20000, description="原始文本（脚本/口播稿/文案）")


class BatchTaskCreateReq(BaseModel):
    name: str = Field(default="", max_length=100)
    topics: list[str] = Field(default_factory=list, max_length=50, description="主题列表（与文件上传二选一）")
    platform: str = Field(default="douyin")
    duration: int = Field(default=60, ge=10, le=300)
    style: str = Field(default="通用", max_length=32)


class RecordUpdateReq(BaseModel):
    topic: str | None = Field(default=None, max_length=100)
    style: str | None = Field(default=None, max_length=32)
    duration: int | None = Field(default=None, ge=10, le=300)
    platform: str | None = Field(default=None, max_length=32)
    status: str | None = None


class TemplateCreateReq(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    scene_type: str = Field(default="prompt", description="script/style/prompt")
    content: str = Field(min_length=5, max_length=20000)
    description: str = Field(default="", max_length=512)


class TemplateUpdateReq(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    scene_type: str | None = None
    content: str | None = Field(default=None, max_length=20000)
    description: str | None = Field(default=None, max_length=512)
