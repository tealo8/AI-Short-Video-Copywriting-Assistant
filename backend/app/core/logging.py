# -*- coding: utf-8 -*-
"""统一日志封装：控制台 + 滚动文件，全链路可溯源。"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings

_LOGGER_NAME = "ai_content_platform"
_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger(_LOGGER_NAME)
    root.setLevel(level)
    root.propagate = False

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # 降噪：三方库告警只保留 WARNING
    for noisy in ("httpx", "httpcore", "urllib3", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str = "app") -> logging.Logger:
    setup_logging()
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
