# -*- coding: utf-8 -*-
"""Ollama 本地模型 Provider：离线免费推理，主 Provider。

走 /api/chat（对话接口，system 与 user 分离，格式更稳定），
format=json 强制结构化输出（Ollama 0.3+ 原生支持），
同时 prompt 层仍要求"只输出 JSON"，双保险应对本地小模型。
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider, LLMSpec

logger = get_logger("llm.ollama")


class OllamaProvider(LLMProvider):
    name = "ollama"

    def _client(self, timeout: int) -> httpx.Client:
        return httpx.Client(base_url=settings.OLLAMA_BASE_URL, timeout=timeout)

    def generate(self, spec: LLMSpec) -> str:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": spec.system},
                {"role": "user", "content": spec.prompt},
            ],
            "stream": False,
            "format": "json" if spec.json_mode else "",
            "options": {
                "temperature": spec.temperature,
                "num_predict": min(spec.max_tokens, settings.LLM_MAX_TOKENS),
                "num_ctx": settings.LLM_CONTEXT_LIMIT,
            },
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        }
        try:
            with self._client(settings.LLM_TIMEOUT) as client:
                resp = client.post("/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "") or ""
        except httpx.HTTPStatusError as exc:
            raise LLMError(f"Ollama 返回错误状态 {exc.response.status_code}", http_status=502) from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama 连接失败: {exc.__class__.__name__}") from exc

    def health(self) -> dict:
        try:
            with self._client(5) as client:
                resp = client.get("/api/tags")
                resp.raise_for_status()
                models = [m.get("name", "") for m in resp.json().get("models", [])]
                if not models:
                    return {"ok": False, "detail": "Ollama 已连接但无任何模型"}
                if settings.OLLAMA_MODEL not in models:
                    return {
                        "ok": False,
                        "detail": f"缺少模型 {settings.OLLAMA_MODEL}（已有: {', '.join(models[:3])}）",
                    }
                return {"ok": True, "detail": f"模型 {settings.OLLAMA_MODEL} 就绪"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": f"Ollama 不可达（{exc.__class__.__name__}）"}
