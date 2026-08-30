# -*- coding: utf-8 -*-
"""结构化输出 Schema：LLM 输出强约束的"契约层"。

前端渲染、Word 导出、历史归档全部依赖此处的字段契约；
Pydantic 校验失败即触发"纠错反馈重试"，从根上杜绝字段缺失/格式混乱。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SegmentSchema(BaseModel):
    """镜头分段：时间精准、类型明确。"""

    index: int = Field(description="分段序号，从 1 开始")
    start_time: str = Field(description="开始时间，格式 MM:SS")
    end_time: str = Field(description="结束时间，格式 MM:SS")
    duration_sec: int = Field(description="本段时长（秒），所有段之和必须等于视频总时长")
    type: str = Field(description="出镜口播 on_camera 或 旁白 narration")
    scene: str = Field(description="画面内容：景别、运镜、素材提示")
    lines: str = Field(description="本段出镜台词/口播内容，口语化")
    subtitle: str = Field(description="字幕重点，≤20字，画面核心信息")


class TitleItemSchema(BaseModel):
    title: str = Field(description="爆款标题")
    tone: str = Field(description="类型：悬念式/干货式/共鸣式/提问式/强化")


class TagSetSchema(BaseModel):
    hot: list[str] = Field(description="热门泛标签 3 个，带#前缀")
    mid: list[str] = Field(description="行业中标签 3 个，带#前缀")
    long: list[str] = Field(description="精准长尾标签 6 个，带#前缀")


class ScriptSchema(BaseModel):
    """短视频脚本完整套装：概述 + 钩子 + 分镜 + 结尾 + 标题 + 标签。

    titles 的 LLM 级下限为 6：7B 级模型直接输出 10 组偶有不稳，
    不足部分由质量修复层按模板确定性补足（最终交付恒为 10 组）。
    """

    topic_overview: str = Field(description="视频主题概述，精简适配平台定位（≤80字）")
    hook: str = Field(description="开头 3 秒爆款钩子（≤40字），适配平台算法")
    segments: list[SegmentSchema] = Field(min_length=3, description="镜头分段脚本")
    ending: str = Field(description="结尾互动引导话术（≤60字），提升完播与互动")
    titles: list[TitleItemSchema] = Field(max_length=10, description="差异化爆款标题（不足 10 组由系统确定性补足）")
    tags: TagSetSchema


class TitleSetSchema(BaseModel):
    titles: list[TitleItemSchema] = Field(max_length=10, description="差异化爆款标题（不足 10 组由系统确定性补足）")
    tags: TagSetSchema


class CopywritingSchema(BaseModel):
    result: str = Field(description="改写后完整正文")
    key_points: list[str] = Field(default_factory=list, description="表达亮点说明，2-4 条")
    changed_count: int = Field(default=0, description="与原稿差异度量化估计 0-100")
