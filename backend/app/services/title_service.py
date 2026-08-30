# -*- coding: utf-8 -*-
"""模块2：多平台爆款标题 & 分层话题标签生成。"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import ContentRecord
from app.services.llm.llm_service import generate_json
from app.services.prompts.builder import build_titles_spec
from app.services.prompts.schemas import TitleSetSchema
from app.services.quality_service import titles_check


def generate_title_set(
    db: Session,
    user_id: int,
    *,
    topic: str,
    platform: str = "douyin",
    action: str = "generate",
    existing_titles: list[str] | None = None,
    demo: bool = False,
    save_record: bool = True,
) -> dict[str, Any]:
    spec = build_titles_spec(topic, platform, action, existing_titles)
    model, provider = generate_json(spec, TitleSetSchema, provider="mock" if demo else None)

    titles, seen = [], set()
    for item in model.titles:
        t = item.title.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        titles.append({"title": t, "tone": item.tone})
    # 不足 10 组：由质量层确定性补足（产品承诺恒为 10 组）
    from app.services.quality_service import _pad_titles
    titles, pad_warnings = _pad_titles(titles, topic)
    tags = model.tags.model_dump()
    tags = {k: list(dict.fromkeys(v)) for k, v in tags.items()}
    warnings = titles_check(titles, tags) + pad_warnings

    record = None
    if save_record and not demo:
        record = ContentRecord(
            user_id=user_id,
            topic=topic,
            record_type="titles",
            platform=platform,
            style="标题&标签",
            duration=0,
            content={"titles": titles, "tags": tags, "action": action,
                     "existing": existing_titles or []},
            titles=[t["title"] for t in titles],
            tags=[{"tier": tier, "text": t} for tier in ("hot", "mid", "long") for t in tags.get(tier, [])],
            source_model=provider,
            status="success",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return {
        "record_id": record.id if record else None,
        "titles": titles,
        "tags": tags,
        "source_model": "demo" if demo else provider,
        "warnings": warnings,
        "demo": demo,
    }
