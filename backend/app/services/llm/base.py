# -*- coding: utf-8 -*-
"""LLM Provider 统一抽象。

所有 Provider 对上层暴露同一契约：generate(spec) -> str（原始文本）。
原始文本的 JSON 抽取、Schema 校验、重试纠错统一由 llm_service 完成，
Provider 只负责"拿到模型原始回复"，职责单一、便于扩展新模型供应商。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMSpec:
    """一次完整的生成请求规格（分层 Prompt 工程产物）。"""

    task: str                      # script | titles | copywriting | ...
    system: str                    # LAYER1 角色与任务
    prompt: str                    # LAYER2-4 参数化变量 + 结构约束 + 输出守则
    json_mode: bool = True         # 是否强制 JSON 输出
    temperature: float = 0.7
    max_tokens: int = 4096
    meta: dict = field(default_factory=dict)  # topic/platform/style/duration 等


class LLMProvider(ABC):
    """Provider 协议：所有实现必须包含 name 与 health。"""

    name: str = "base"

    @abstractmethod
    def generate(self, spec: LLMSpec) -> str:
        """执行一次生成，返回模型原始文本（不含任何解析）。"""

    @abstractmethod
    def health(self) -> dict:
        """探测可用性：{ok, detail}，用于状态页与降级决策。"""
