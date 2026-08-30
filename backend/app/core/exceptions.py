# -*- coding: utf-8 -*-
"""全局异常体系：业务异常统一携带 code，避免裸 Exception 泄漏。"""
from __future__ import annotations


class AppError(Exception):
    """平台业务异常基类。"""

    code: int = 1000      # 业务错误码
    http_status: int = 400
    message: str = "业务处理失败"

    def __init__(self, message: str | None = None, *, code: int | None = None, http_status: int | None = None):
        if message:
            self.message = message
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        super().__init__(self.message)


class ParamError(AppError):
    code = 1001
    http_status = 422
    message = "请求参数校验失败"


class AuthError(AppError):
    code = 1002
    http_status = 401
    message = "未登录或登录已过期"


class PermissionError_(AppError):
    code = 1003
    http_status = 403
    message = "无权访问该资源"


class NotFoundError(AppError):
    code = 1004
    http_status = 404
    message = "资源不存在"


class LLMError(AppError):
    """AI 能力层异常：模型不可用 / 输出不合规 / 降级失败。"""
    code = 2001
    http_status = 502
    message = "AI 服务暂时不可用，请稍后重试"


class LLMOutputError(AppError):
    """模型输出不满足结构化约束（重试后仍失败）。"""
    code = 2002
    http_status = 502
    message = "AI 输出格式校验未通过，请重试或更换模型"


class RateLimitError(AppError):
    code = 2003
    http_status = 429
    message = "请求过于频繁，请稍后再试"


class StoreError(AppError):
    code = 3001
    http_status = 500
    message = "数据持久化失败"
