# -*- coding: utf-8 -*-
"""统一接口响应格式：{code, message, data}，前端按 code 统一处理。"""
from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, http_status: int = 400, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"code": code, "message": message, "data": data},
    )
