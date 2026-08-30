# -*- coding: utf-8 -*-
"""云端 OpenAI 兼容 Provider：DeepSeek / 通义千问 / OpenAI 一接口通吃。

base_url 指向兼容根地址（如 https://api.deepseek.com），
内部拼接 /v1/chat/completions；response_format=json_object 强约束输出。
"""
from __future__ import annotations

import httpx

from app.config import settings
from app.core.exceptions import LLMError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider, LLMSpec

logger = get_logger("llm.cloud")


class CloudProvider(LLMProvider):
    name = "cloud"

    @property
    def available(self) -> bool:
        return bool(settings.CLOUD_API_KEY)

    def _client(self, timeout: int) -> httpx.Client:
        return httpx.Client(
            base_url=settings.CLOUD_BASE_URL.rstrip("/"),
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {settings.CLOUD_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    def generate(self, spec: LLMSpec) -> str:
        if not self.available:
            raise LLMError("云端模型未配置 API Key（CLOUD_API_KEY 为空）")
        payload = {
            "model": settings.CLOUD_MODEL,
            "messages": [
                {"role": "system", "content": spec.system},
                {"role": "user", "content": spec.prompt},
            ],
            "temperature": spec.temperature,
            "max_tokens": min(spec.max_tokens, settings.LLM_MAX_TOKENS),
        }
        if spec.json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            with self._client(settings.CLOUD_TIMEOUT) as client:
                resp = client.post("/v1/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"] or ""
        except httpx.HTTPStatusError as exc:
            # 401=Key 无效 / 429=限流 / 5xx=服务端波动 → 均触发降级
            raise LLMError(f"云端接口返回 {exc.response.status_code}", http_status=502) from exc
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            raise LLMError(f"云端接口调用失败: {exc.__class__.__name__}") from exc

    def health(self) -> dict:
        if not self.available:
            return {"ok": False, "detail": "未配置 CLOUD_API_KEY"}
        return {"ok": True, "detail": f"云端 {settings.CLOUD_MODEL} 已配置"}
