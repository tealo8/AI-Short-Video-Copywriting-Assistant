# -*- coding: utf-8 -*-
"""模块1：AI 短视频脚本生成（核心服务）。

骨架：参数校验 -> 分层 Prompt -> LLM 结构化生成 -> 质量修复 -> TTS 配音稿 ->
标题/标签归档 -> 持久化 ContentRecord -> 返回完整套装。
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import LLMOutputError
from app.core.logging import get_logger
from app.db.models import ContentRecord
from app.services.llm.llm_service import generate_json
from app.services.prompts.builder import build_script_spec_llm
from app.services.prompts.schemas import ScriptSchema
from app.services.quality_service import repair_script
from app.services.tts_service import script_lines_to_tts

logger = get_logger("service.script")

VALID_PLATFORMS = ("douyin", "xiaohongshu", "shipinhao", "bilibili")
VALID_STYLES = (
    "通用", "小红书温柔种草风", "抖音口播干货风", "正式专业科普风",
    "幽默轻松段子风", "电商带货营销风", "极简高级短句风",
)


def validate_script_params(topic: str, platform: str, duration: int, style: str) -> None:
    from app.core.exceptions import ParamError

    topic = topic.strip()
    if not (2 <= len(topic) <= 100):
        raise ParamError("主题长度需在 2-100 字之间")
    if platform not in VALID_PLATFORMS:
        raise ParamError(f"平台类型非法，可选: {', '.join(VALID_PLATFORMS)}")
    if not (10 <= int(duration) <= 300):
        raise ParamError("时长需在 10-300 秒之间")
    if style not in VALID_STYLES:
        raise ParamError(f"风格非法，可选: {', '.join(VALID_STYLES)}")


def validate_script_params(topic: str, platform: str, duration: int, style: str,
                           word_budget: tuple[int | None, int | None] | None = None) -> None:
    from app.core.exceptions import ParamError

    topic = topic.strip()
    if not (2 <= len(topic) <= 100):
        raise ParamError("主题长度需在 2-100 字之间")
    if platform not in VALID_PLATFORMS:
        raise ParamError(f"平台类型非法，可选: {', '.join(VALID_PLATFORMS)}")
    if not (10 <= int(duration) <= 300):
        raise ParamError("时长需在 10-300 秒之间")
    if style not in VALID_STYLES:
        raise ParamError(f"风格非法，可选: {', '.join(VALID_STYLES)}")
    if word_budget:
        lo, hi = word_budget
        if (lo and (lo < 20 or lo > 800)) or (hi and (hi < 20 or hi > 1000)):
            raise ParamError("字数范围需在 20-1000 之间")
        if lo and hi and lo > hi:
            raise ParamError("字数下限不能大于上限")


def generate_script(
    db: Session,
    user_id: int,
    *,
    topic: str,
    platform: str = "douyin",
    duration: int = 60,
    style: str = "通用",
    custom_style: str = "",
    word_budget_min: int | None = None,
    word_budget_max: int | None = None,
    demo: bool = False,
    save_record: bool = True,
) -> dict[str, Any]:
    """完整链路：生成 -> 修复 -> 存档 -> 返回套装。

    demo=True 时直连 Mock Provider（演示数据，不落库、不消耗模型），
    word_budget_min/max 可约束口播台词字数范围。
    """
    word_budget = (word_budget_min, word_budget_max) if (word_budget_min or word_budget_max) else None
    validate_script_params(topic, platform, duration, style, word_budget)

    spec = build_script_spec_llm(topic, platform, duration, style, custom_style, word_budget)
    model, provider = generate_json(spec, ScriptSchema, provider="mock" if demo else None)
    script = model.model_dump()

    try:
        script, warnings = repair_script(script, duration, topic)
    except ValueError as exc:
        raise LLMOutputError(str(exc)) from exc

    tts = script_lines_to_tts(script["segments"])
    titles = [t["title"] for t in script["titles"]]
    tags: list[dict] = [
        {"tier": tier, "text": t}
        for tier in ("hot", "mid", "long")
        for t in script["tags"].get(tier, [])
    ]
    overview = str(script["topic_overview"])
    hook, ending = str(script["hook"]), str(script["ending"])
    body_text = (
        f"【主题概述】\n{overview}\n\n【爆款钩子】\n{hook}\n\n【分镜脚本】\n"
        + "\n".join(
            f"{s['index']}. [{s['start_time']}-{s['end_time']}|{s['type']}] {s['scene']} 台词：{s['lines']}"
            for s in script["segments"]
        )
        + f"\n\n【结尾互动】\n{ending}"
    )

    record = None
    if save_record and not demo:
        record = ContentRecord(
            user_id=user_id,
            topic=topic,
            record_type="script",
            platform=platform,
            style=style,
            duration=duration,
            content=script,
            titles=titles,
            tags=tags,
            tts_text=tts["text"],
            body_text=body_text,
            source_model=provider,
            status="success",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    return {
        "record_id": record.id if record else None,
        "topic": topic,
        "platform": platform,
        "duration": duration,
        "style": style,
        "overview": overview,
        "hook": hook,
        "segments": script["segments"],
        "ending": ending,
        "titles": titles,
        "title_items": script["titles"],
        "tags": tags,
        "tts_text": tts["text"],
        "tts_meta": {k: tts[k] for k in ("mode", "total_chars", "est_duration_sec", "sentences")},
        "body_text": body_text,
        "source_model": "demo" if demo else provider,
        "warnings": warnings,
        "demo": demo,
    }
