# -*- coding: utf-8 -*-
"""API v1 路由聚合。"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (admin, auth, batch, copywriting, export, history, script,
                        system, templates, titles, tts)

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(script.router)
router.include_router(titles.router)
router.include_router(copywriting.router)
router.include_router(tts.router)
router.include_router(batch.router)
router.include_router(history.router)
router.include_router(templates.router)
router.include_router(export.router)
router.include_router(system.router)
router.include_router(admin.router)
