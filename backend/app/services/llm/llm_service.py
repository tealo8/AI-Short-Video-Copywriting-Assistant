# -*- coding: utf-8 -*-
"""LLM 高层服务：结构化输出强约束 + 超时重试 + Token 截断 + 降级，一站式收口。

generate_json(spec, schema)：
 1. 走 Provider 链拿原始文本（Router 内含重试与降级）；
 2. 防御性解析 + Schema 校验；
 3. 首次校验失败 → 带错误信息反馈重试 1 次（模型自纠错）；
 4. 二次失败 → 抛 LLMOutputError（不静默降级，保证数据可信）。
"""
from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.core.exceptions import LLMOutputError
from app.core.logging import get_logger
from app.services.llm.base import LLMSpec
from app.services.llm.json_utils import extract_json_text, parse_and_validate
from app.services.llm.router import router

logger = get_logger("llm.service")

T = TypeVar("T", bound=BaseModel)


def generate_json(spec: LLMSpec, schema: type[T], provider: str | None = None) -> tuple[T, str]:
    """返回 (校验通过的结构化对象, 实际使用的 provider_name)。

    provider 指定时直连该 Provider（如 demo 模式直达 mock），否则走降级链。
    """
    raw, provider_name = (
        router.generate_raw_from(spec, provider) if provider else router.generate_raw(spec)
    )

    try:
        model = parse_and_validate(raw, schema, task=spec.task)
        return model, provider_name
    except LLMOutputError as first_err:
        logger.warning("LLM 输出首次校验失败 task=%s provider=%s: %s", spec.task, provider_name, first_err.message)
        # 纠错反馈重试：把原始输出 + 错误原因回喂模型
        feedback = (
            f"你上次的输出未通过校验：{first_err.message}\n"
            f"上次输出片段：{extract_json_text(raw)[:600]}\n"
            f"请重新输出，必须严格符合上文格式要求，只输出 JSON 对象，不要任何其他文字。"
        )
        retry_prompt = f"{spec.prompt}\n\n【重要】{feedback}"
        retry_spec = LLMSpec(
            task=spec.task, system=spec.system, prompt=retry_prompt,
            json_mode=spec.json_mode, temperature=max(0.2, spec.temperature - 0.3),
            max_tokens=spec.max_tokens, meta=spec.meta,
        )
        raw2, provider2 = (
            router.generate_raw_from(retry_spec, provider) if provider else router.generate_raw(retry_spec)
        )
        model = parse_and_validate(raw2, schema, task=spec.task)  # 仍失败则抛 LLMOutputError
        return model, provider2


def generate_text(spec: LLMSpec) -> tuple[str, str]:
    """非 JSON 任务（如纯文本优化）直接返回原文。"""
    return router.generate_raw(spec)
