# -*- coding: utf-8 -*-
"""模块3：智能文案编辑器（改写/扩写/缩写/风格迁移/润色/纠错/原创度提升）。"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ParamError
from app.db.models import ContentRecord
from app.services.llm.llm_service import generate_json
from app.services.prompts.builder import build_copywriting_spec
from app.services.prompts.schemas import CopywritingSchema

VALID_ACTIONS = ("rewrite", "expand", "condense", "style_transfer", "polish", "proofread", "dedupe")
VALID_STYLES = (
    "通用", "小红书温柔种草风", "抖音口播干货风", "正式专业科普风",
    "幽默轻松段子风", "电商带货营销风", "极简高级短句风",
)


def transform_text(
    db: Session,
    user_id: int,
    *,
    text: str,
    action: str = "rewrite",
    style: str = "通用",
    custom_style: str = "",
    demo: bool = False,
    save_record: bool = True,
) -> dict[str, Any]:
    text = (text or "").strip()
    if len(text) < 10:
        raise ParamError("原文过短，至少 10 字")
    if len(text) > 5000:
        raise ParamError("原文过长，请控制在 5000 字以内")
    if action not in VALID_ACTIONS:
        raise ParamError(f"操作类型非法，可选: {', '.join(VALID_ACTIONS)}")
    if style not in VALID_STYLES and not custom_style:
        raise ParamError(f"风格非法，可选: {', '.join(VALID_STYLES)}")

    spec = build_copywriting_spec(text, action, style, custom_style)
    model, provider = generate_json(spec, CopywritingSchema, provider="mock" if demo else None)
    result = model.result.strip()

    record = None
    if save_record and not demo:
        record = ContentRecord(
            user_id=user_id,
            topic=text[:24] + ("…" if len(text) > 24 else ""),
            record_type="copywriting",
            platform="",
            style=style if not custom_style else f"自定义-{custom_style[:20]}",
            duration=0,
            content={"action": action, "key_points": model.key_points,
                     "changed_count": model.changed_count},
            body_text=result,
            source_model=provider,
            status="success",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return {
        "record_id": record.id if record else None,
        "result": result,
        "key_points": model.key_points,
        "changed_count": model.changed_count,
        "action": action,
        "style": style,
        "source_model": "demo" if demo else provider,
        "demo": demo,
    }
