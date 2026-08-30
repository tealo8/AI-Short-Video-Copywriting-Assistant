# -*- coding: utf-8 -*-
"""双模型智能适配与降级路由。

核心逻辑：按配置的 Provider 优先级链（默认 ollama -> cloud -> mock）顺序尝试；
- 网络类失败（超时/断连/5xx）→ 单 Provider 内重试 settings.LLM_RETRIES 次后降级到下一家；
- 输出不合规（JSON 解析/Schema 失败）→ 由上层 llm_service 做"输出纠错反馈重试"，
  仍失败才升级为 LLMOutputError 并向下游报告（不静默降级到 mock，避免数据失真）；
- 全链失败时若链尾为 mock 则兜底演示数据，保障 7×24 可用。
"""
from __future__ import annotations

from app.config import settings
from app.core.exceptions import LLMError, LLMOutputError
from app.core.logging import get_logger
from app.services.llm.base import LLMProvider, LLMSpec
from app.services.llm.cloud_provider import CloudProvider
from app.services.llm.mock_provider import MockProvider
from app.services.llm.ollama_provider import OllamaProvider

logger = get_logger("llm.router")

_REGISTRY: dict[str, type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "cloud": CloudProvider,
    "mock": MockProvider,
}


class LLMRouter:
    def __init__(self) -> None:
        self.reload()

    def reload(self) -> None:
        """按当前配置重建 Provider 链（运行时配置变更后调用）。"""
        self._providers: dict[str, LLMProvider] = {}
        for name in settings.provider_chain:
            cls = _REGISTRY.get(name)
            if cls is None:
                logger.warning("未知 Provider 已跳过: %s", name)
                continue
            self._providers[name] = cls()
        logger.info("Provider 链重建完成: %s", self.chain)

    @property
    def chain(self) -> list[str]:
        return list(self._providers.keys())

    def generate_raw(self, spec: LLMSpec) -> tuple[str, str]:
        """按优先级链执行，返回 (原始文本, provider_name)。全链失败抛 LLMError。"""
        last_error: Exception | None = None
        for name in self.chain:
            try:
                return self._try_provider(name, spec)
            except LLMOutputError:
                raise
            except LLMError as exc:
                last_error = exc
        detail = f"全部 Provider 不可用（链: {self.chain}）"
        if last_error:
            detail += f"；最后错误: {getattr(last_error, 'message', last_error)}"
        raise LLMError(detail)

    def generate_raw_from(self, spec: LLMSpec, provider_name: str) -> tuple[str, str]:
        """指定 Provider 直连（演示数据 / 白名单测试等场景），不再走降级链。"""
        if provider_name not in self._providers:
            available = ", ".join(self.chain) or "无可用 Provider"
            raise LLMError(f"Provider {provider_name} 未启用（当前链: {available}）", code=2001)
        return self._try_provider(provider_name, spec)

    def _try_provider(self, name: str, spec: LLMSpec) -> tuple[str, str]:
        provider = self._providers[name]
        last_error: Exception | None = None
        for attempt in range(1, settings.LLM_RETRIES + 1):
            try:
                import time
                t0 = time.time()
                text = provider.generate(spec)
                logger.info(
                    "LLM 调用成功 provider=%s attempt=%d cost=%.1fs task=%s",
                    name, attempt, (time.time() - t0), spec.task,
                )
                return text, name
            except LLMOutputError:
                raise  # 输出不合规：交由上层做纠错重试，不在此处降级
            except LLMError as exc:
                last_error = exc
                logger.warning("LLM provider=%s attempt=%d 失败: %s", name, attempt, exc.message)
                continue
            except Exception as exc:  # noqa: BLE001 防御：Provider 内部任何异常
                last_error = LLMError(f"{exc.__class__.__name__}: {exc}")
                logger.exception("LLM provider=%s 未知异常", name)
                continue
        raise last_error or LLMError(f"Provider {name} 调用失败")

    def status(self) -> dict:
        """各级健康状态，供 /system/status 与前端展示。"""
        results = []
        for name, provider in self._providers.items():
            try:
                h = provider.health()
            except Exception as exc:  # noqa: BLE001
                h = {"ok": False, "detail": f"探测异常 {exc.__class__.__name__}"}
            results.append({"provider": name, **h})
        active = next((r["provider"] for r in results if r["ok"]), None)
        return {
            "chain": self.chain,
            "providers": results,
            "active_provider": active,
            "model_default": settings.OLLAMA_MODEL,
        }


router = LLMRouter()
