# -*- coding: utf-8 -*-
"""
AI 短视频&文案智能生产平台 - 全局配置
所有环境相关配置统一抽离，支持 .env 覆盖，容器化部署零改动。
"""
"""Level 基类：BaseSettings 与运行时覆盖。"""
import json as _json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
RUNTIME_OVERRIDE_FILE = BASE_DIR / "data" / "runtime_settings.json"

# 允许运行时热更新的配置键（前端模型配置弹窗可修改）
RUNTIME_EDITABLE = (
    "LLM_PROVIDER_PRIORITY", "LLM_TEMPERATURE", "LLM_MAX_TOKENS", "LLM_RETRIES", "LLM_TIMEOUT",
    "OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_KEEP_ALIVE",
    "CLOUD_BASE_URL", "CLOUD_API_KEY", "CLOUD_MODEL", "CLOUD_TIMEOUT",
    "BATCH_MAX_WORKERS", "BATCH_ITEM_LIMIT",
)


def _load_runtime_overrides() -> dict:
    """启动时合并运行时覆盖（data/runtime_settings.json，无则跳过）。"""
    try:
        if RUNTIME_OVERRIDE_FILE.exists():
            return _json.loads(RUNTIME_OVERRIDE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 覆盖文件损坏不应阻断启动
        pass
    return {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 应用 ----------
    APP_NAME: str = "AI 一站式短视频&文案智能生产平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = str(BASE_DIR / "logs")

    # ---------- 安全 ----------
    SECRET_KEY: str = "change-me-in-production-8f2c9d1e7a"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # ---------- 数据库（SQLite 本地 / MySQL 线上） ----------
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'app.db').as_posix()}"

    # ---------- AI 能力层：Provider 优先级链 ----------
    # 顺序即降级顺序：ollama -> cloud -> mock，逗号分隔，可自由裁剪
    LLM_PROVIDER_PRIORITY: str = "ollama,cloud,mock"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096        # Token 截断上限
    LLM_CONTEXT_LIMIT: int = 8192     # 上下文保护线
    LLM_RETRIES: int = 2              # 单 Provider 失败重试次数
    LLM_TIMEOUT: int = 180            # 单次请求超时（秒）

    # ---------- Ollama 本地模型（默认主 Provider） ----------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_KEEP_ALIVE: str = "5m"

    # ---------- 云端 OpenAI 兼容接口（DeepSeek / 通义 / OpenAI 通用） ----------
    CLOUD_BASE_URL: str = "https://api.deepseek.com"   # 兼容接口根地址
    CLOUD_API_KEY: str = ""
    CLOUD_MODEL: str = "deepseek-chat"
    CLOUD_TIMEOUT: int = 120

    # ---------- 批量异步任务 ----------
    BATCH_MAX_WORKERS: int = 2        # 并发生成线程数（保护本地模型压测）
    BATCH_ITEM_LIMIT: int = 50        # 单任务最大条目数

    # ---------- 内容质量规则 ----------
    TTS_MAX_SENTENCE_LEN: int = 42    # 配音分句最长字符数
    MIN_SCRIPT_SEGMENTS: int = 3      # 脚本最少分段数

    @property
    def provider_chain(self) -> list[str]:
        return [p.strip().lower() for p in self.LLM_PROVIDER_PRIORITY.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
# 启动时合并运行时覆盖（前端配置弹窗写入的值优先于 .env，- 仅影响本机运行）
try:
    if _load_runtime_overrides():
        for _k, _v in _load_runtime_overrides().items():
            if _k in RUNTIME_EDITABLE:
                setattr(settings, _k, _v)
except Exception:  # noqa: BLE001
    pass


def apply_runtime_overrides(overrides: dict) -> list[str]:
    """应用并持久化运行时配置（前端模型配置弹窗）。返回实际生效的键列表。"""
    applied = []
    for key, value in overrides.items():
        if key not in RUNTIME_EDITABLE or value is None:
            continue
        if isinstance(value, str):
            value = value.strip()
            if key == "LLM_PROVIDER_PRIORITY" and not value:
                continue
        setattr(settings, key, value)
        applied.append(key)
    if applied:
        RUNTIME_OVERRIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
        RUNTIME_OVERRIDE_FILE.write_text(
            _json.dumps({k: getattr(settings, k) for k in RUNTIME_EDITABLE}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return applied


def get_runtime_overrides() -> dict:
    return {k: getattr(settings, k) for k in RUNTIME_EDITABLE}


def mask_secret(api_key: str) -> str:
    """前端展示时脱敏 API Key。"""
    if not api_key:
        return ""
    return api_key[:4] + "****" + api_key[-4:] if len(api_key) > 10 else "****"
