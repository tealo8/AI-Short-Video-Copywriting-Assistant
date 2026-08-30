# -*- coding: utf-8 -*-
"""内容质量检测与自动修复（模块：质量护栏）。

两条路径：
- 硬修复：会真实改写数据（时长对齐、序号重排、字幕截断、标题去重、标签规范化）；
- 软警告：只上报给前端（字数偏差、镜头密度、类型占比），由用户决策。
"""
from __future__ import annotations

import re
from typing import Any

from app.config import settings

_VALID_TYPES = {"on_camera", "narration"}

# 标签补足模板（模型输出不足时确定性兜底，保证"3+3+6 配比"）
_TIER_TARGETS = {"hot": 3, "mid": 3, "long": 6}
_TIER_POOL = {
    "hot": ["#热门", "#上热门", "#分享"],
    "mid": ["#干货分享", "#涨知识", "#短视频"],
    "long": ["#新手入门", "#攻略", "#效率工具", "#经验分享", "#避坑指南", "#收藏"],
}


def _pad_tags(tags: dict[str, list[str]], topic: str) -> dict[str, list[str]]:
    for tier, target in _TIER_TARGETS.items():
        items = tags.get(tier) or []
        if len(items) < target:
            pool = [f"#{topic[:12]}", *_TIER_POOL[tier]]
            for cand in pool:
                if len(items) >= target:
                    break
                if cand not in items:
                    items.append(cand)
        tags[tier] = items
    return tags


# 标题补足模板（模型输出不足 10 组时的确定性兜底，保证交付"10 组"承诺）
_PAD_TITLE_TEMPLATES = [
    "{topic}，我建议你慎入",
    "看完这条视频，{topic}少走弯路",
    "{topic}小白必看 | 3 分钟讲透",
    "别再交智商税了！{topic}真相",
    "{topic}从入门到进阶，一篇讲完",
    "刷到就是缘分：{topic}干货合集",
    "普通人也能做的{topic}，你敢信？",
    "{topic}万能公式，收藏这一条就够",
]


def _pad_titles(titles: list[dict], topic: str) -> tuple[list[dict], list[str]]:
    """不足 10 组时用确定性模板补足并去重；返回 (titles, warnings)。"""
    if len(titles) >= 10:
        return titles[:10], []
    seen = {t["title"] for t in titles}
    warnings = [f"模型输出标题 {len(titles)} 组，已按模板补足至 10 组"]
    for tmpl in _PAD_TITLE_TEMPLATES:
        if len(titles) >= 10:
            break
        cand = tmpl.format(topic=topic[:18])
        if cand in seen:
            continue
        seen.add(cand)
        titles.append({"title": cand, "tone": "干货式"})
    return titles, warnings


def _fmt(sec: int) -> str:
    return f"{sec // 60:02d}:{sec % 60:02d}"


def repair_script(script: dict[str, Any], duration: int, topic: str = "") -> tuple[dict[str, Any], list[str]]:
    """对模型产出的脚本执行修复 + 质检，返回 (修复后数据, 警告列表)。"""
    warnings: list[str] = []

    # ---------- 1. 标题去重（保留前 10 个不重复） ----------
    titles, seen = [], set()
    for item in script.get("titles", []):
        t = item["title"].strip() if isinstance(item, dict) else str(item).strip()
        if not t or t in seen:
            continue
        seen.add(t)
        if isinstance(item, dict):
            titles.append({"title": t, "tone": item.get("tone", "干货式")})
        else:
            titles.append({"title": t, "tone": "干货式"})
    if len(titles) < 5:
        warnings.append(f"标题数量仅 {len(titles)} 组，建议 10 组")
    titles, pad_warnings = _pad_titles(titles, topic or "内容")
    warnings.extend(pad_warnings)
    script["titles"] = titles[:10]

    # ---------- 2. 标签规范化 ----------
    tag_source = script.get("tags") or {}
    if isinstance(tag_source, dict):
        for tier in ("hot", "mid", "long"):
            items = tag_source.get(tier) or []
            items = [
                (t if str(t).startswith("#") else f"#{t}").strip().replace("##", "#")
                for t in items
            ]
            items = list(dict.fromkeys(items))  # 去重保序
            if not items and tier == "hot":
                items = ["#热门"]
            elif not items and tier == "mid":
                items = ["#干货"]
            elif not items:
                items = ["#内容创作"]
            tag_source[tier] = items
    tag_source = _pad_tags(tag_source, topic or "内容")
    script["tags"] = tag_source

    # ---------- 3. 分段修复：序号、时长对齐 ----------
    segments = script.get("segments") or []
    total = sum(int(s.get("duration_sec", 0)) for s in segments)
    if not segments:
        raise ValueError("脚本缺少分段数据")
    if total < 20:
        warnings.append(f"镜头分段总时长异常（{total}s），已按 {duration}s 重排")
    # 时长对齐：差值修正到最长的一段（保证总和 == duration）
    if total != duration:
        diff = duration - total
        idx = max(range(len(segments)), key=lambda i: segments[i].get("duration_sec", 0))
        segments[idx]["duration_sec"] = max(3, int(segments[idx].get("duration_sec", 10)) + diff)
        warnings.append(f"分段总时长 {total}s 与要求 {duration}s 不一致，已自动对齐")

    cursor = 0
    for i, seg in enumerate(segments):
        if seg.get("type") not in _VALID_TYPES:
            seg["type"] = "narration"
            warnings.append(f"第 {i + 1} 段镜头类型非法，已修正为旁白")
        seg["index"] = i + 1
        dur = max(3, int(seg.get("duration_sec", 10)))
        seg["duration_sec"] = dur
        seg["start_time"] = _fmt(cursor)
        seg["end_time"] = _fmt(cursor + dur)
        cursor += dur
        sub = str(seg.get("subtitle", "")).strip()
        if len(sub) > 30:
            seg["subtitle"] = sub[:30]
            warnings.append(f"第 {i + 1} 段字幕超过 30 字，已截断")
        if "```" in str(seg.get("lines", "")) or "```" in sub:
            seg["lines"] = str(seg.get("lines", "")).replace("```", "").strip()
    script["segments"] = segments

    # ---------- 4. 钩子/结尾文本洁化 ----------
    script["hook"] = str(script.get("hook", "")).replace("\n", " ").strip("。")
    script["ending"] = str(script.get("ending", "")).replace("\n", " ").strip()
    if len(script["hook"]) > 45:
        warnings.append(f"钩子偏长（{len(script['hook'])} 字），建议 40 字内")

    # ---------- 5. 字数预算检查（软警告） ----------
    lines_text = "".join(s.get("lines", "") for s in segments)
    budget = duration * 4.0
    ratio = len(lines_text) / budget if budget else 1
    if ratio > 1.4:
        warnings.append(f"台词总量 {len(lines_text)} 字，超出 {duration}s 语速预算约 {int((ratio - 1) * 100)}%")
    elif ratio < 0.6:
        warnings.append(f"台词偏少（{len(lines_text)} 字），成片可能不够紧凑")

    return script, warnings


def titles_check(titles: list[dict], tags: dict) -> list[str]:
    warnings = []
    if len(titles) != 10:
        warnings.append(f"标题应为 10 组，当前 {len(titles)} 组")
    tones = [t.get("tone", "") for t in titles]
    for tone in ("悬念式", "干货式", "共鸣式", "提问式"):
        if tones.count(tone) == 0:
            warnings.append(f"缺少「{tone}」类型标题")
    return warnings


def has_markdown(text: str) -> bool:
    return bool(re.search(r"```|^\s*#{1,6}\s", text or ""))
