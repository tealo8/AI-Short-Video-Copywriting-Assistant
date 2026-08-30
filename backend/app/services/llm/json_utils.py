# -*- coding: utf-8 -*-
"""模型原始输出 -> 合法结构化数据 的防御性解析层。

解决行业通病：模型爱包 ```json 围栏、爱在 JSON 前后追加解释、
爱截断输出导致 JSON 半残。此处做：围栏剥离 -> 大括号围栏裁剪 ->
json.loads -> pydantic 校验，任一步失败给出可读原因。
"""
from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.core.exceptions import LLMOutputError

T = TypeVar("T", bound=BaseModel)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_text(raw: str) -> str:
    """从模型回复中抽取最可能的 JSON 片段。"""
    if not raw or not raw.strip():
        raise LLMOutputError("模型返回了空内容")
    text = raw.strip()

    # 1) 剥离 markdown 围栏
    fence = _FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()

    # 2) 裁剪至首个 { 与末个 }（按深层括号扫描保证成对闭合）
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMOutputError("模型输出中未找到 JSON 对象")
    candidate = text[start : end + 1]

    # 3) 深度括号扫描：若外层未闭合，尝试回退到最深的合法片段
    depth, valid_end = 0, -1
    for i, ch in enumerate(candidate):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and valid_end < i:
                valid_end = i
    if valid_end >= 0:
        candidate = candidate[: valid_end + 1]
    return candidate


def parse_and_validate(raw: str, schema: type[T], *, task: str = "") -> T:
    """抽取 + 解析 + Schema 强校验；失败给出字段级原因，便于反馈重试。"""
    text = extract_json_text(raw)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMOutputError(f"JSON 解析失败（{exc.msg}），原始片段: {text[:120]}...") from exc
    if not isinstance(data, dict):
        raise LLMOutputError("JSON 根节点必须为对象")
    try:
        return schema(**data)
    except ValidationError as exc:
        issues = [
            f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}"
            for e in exc.errors()[:5]
        ]
        raise LLMOutputError("Schema 校验失败 -> " + "; ".join(issues)) from exc


def compact_json_lines(text: str) -> list[str]:
    """把模型输出按行切分，仅保留看起来像 JSON 的行（辅助诊断）。"""
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith(("{", "[", '"'))]
