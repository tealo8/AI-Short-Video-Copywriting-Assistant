# -*- coding: utf-8 -*-
"""FastAPI 应用入口：全局异常捕获 / 统一响应 / 路由挂载 / CORS。"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.config import settings
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.response import fail
from app.db.database import init_db

logger = get_logger("main")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 一站式短视频&文案智能生产平台 - 后端服务",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 生产环境建议收敛为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    logger.warning("业务异常 code=%s msg=%s", exc.code, exc.message)
    return fail(exc.code, exc.message, http_status=exc.http_status)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    errors = "; ".join(f"{'.'.join(str(l) for l in e['loc'][1:])}: {e['msg']}" for e in exc.errors()[:5])
    return fail(1001, f"参数校验失败：{errors}", http_status=422)


@app.exception_handler(Exception)
async def global_handler(_: Request, exc: Exception):
    logger.exception("未捕获异常: %s", exc.__class__.__name__)
    return fail(5000, "服务器开小差了，请稍后重试", http_status=500)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("数据库初始化完成: %s", settings.DATABASE_URL)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


app.include_router(v1_router)
