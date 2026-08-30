# -*- coding: utf-8 -*-
"""系统状态接口：模型链健康探测 + 运行时配置可视化读写。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.config import get_runtime_overrides, mask_secret, settings
from app.core.exceptions import ParamError
from app.core.response import ok
from app.services.llm.router import router as llm_router
from app.config import RUNTIME_EDITABLE

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/status")
def status(user: dict = Depends(get_current_user)):
    return ok({
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm": llm_router.status(),
        "batch_max_workers": settings.BATCH_MAX_WORKERS,
        "db": "ok",
        "user": user,
    })


@router.get("/config")
def get_config(user: dict = Depends(get_current_user)):
    """返回全部可编辑配置（云 Key 脱敏）。"""
    cfg = get_runtime_overrides()
    cfg["CLOUD_API_KEY"] = mask_secret(cfg.get("CLOUD_API_KEY", ""))
    cfg["_editable"] = list(RUNTIME_EDITABLE)
    return ok(cfg)


@router.post("/config")
def update_config(payload: dict, user: dict = Depends(get_current_user)):
    """热更新配置（修改后立即生效，无需重启）：Provider 链/模型地址/Key/参数。"""
    from app.config import apply_runtime_overrides
    from app.services.llm.router import router as llm_router

    if not isinstance(payload, dict):
        raise ParamError("配置格式错误")
    applied = apply_runtime_overrides(payload)
    if not applied:
        raise ParamError("没有可更新的配置项")
    llm_router.reload()  # 配置变更后重建 Provider 链
    return ok({"applied": applied}, message="配置已更新并生效")
