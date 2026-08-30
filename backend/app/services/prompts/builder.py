# -*- coding: utf-8 -*-
"""分层 Prompt 组装器：业务服务只传语义参数，Prompt 细节全部封装于此。"""
from __future__ import annotations

from app.config import settings
from app.services.llm.base import LLMSpec
from app.services.prompts.templates import PLATFORM_PROFILES, STYLE_PROFILES, build_script_spec

_TITLE_SCHEMA_HINT = """【输出 JSON 结构】
{
  "titles": [{"title": "标题", "tone": "悬念式|干货式|共鸣式|提问式"}],
  "tags": {"hot": ["#","#","#"], "mid": ["#","#","#"], "long": ["#","#","#","#","#","#"]}
}"""


def build_script_spec_llm(
    topic: str, platform: str, duration: int, style: str, custom_style: str = "",
    word_budget: tuple[int | None, int | None] | None = None,
) -> LLMSpec:
    system, prompt = build_script_spec(topic, platform, duration, style, custom_style, word_budget)
    return LLMSpec(
        task="script", system=system, prompt=prompt, json_mode=True,
        temperature=settings.LLM_TEMPERATURE, max_tokens=settings.LLM_MAX_TOKENS,
        meta={"topic": topic, "platform": platform, "duration": duration, "style": style,
              "word_budget": list(word_budget) if word_budget else None},
    )


def build_titles_spec(
    topic: str, platform: str, action: str = "generate", existing_titles: list[str] | None = None
) -> LLMSpec:
    p = PLATFORM_PROFILES.get(platform, PLATFORM_PROFILES["douyin"])
    system = (
        "你是深谙各平台算法与用户心理的爆款标题专家，擅长产出高点击率、强差异化的标题矩阵与分层标签矩阵。"
    )
    if action == "polish" and existing_titles:
        noise = "\n".join(f"- {t}" for t in existing_titles[:10])
        prompt = f"""请对以下已有标题进行二次润色与强化，保持原有信息点，但提升点击欲与差异化。

【目标平台】{p['label']}（{p['title_style']}）
【主题】{topic}
【已有标题】
{noise}

要求：
1. 输出 10 个升级版标题，避免与原文重复，句式可改写、换角度、加情绪钩子；
2. 同时给出 3 个热门泛标签 + 3 个行业中标签 + 6 个精准长尾标签，带#前缀。

{_TITLE_SCHEMA_HINT}"""
    else:
        prompt = f"""请为主题「{topic}」创作 10 个差异化爆款标题与分层话题标签。

【目标平台】{p['label']}（{p['title_style']}）
【标题要求】
1. 10 个标题完全差异化，覆盖：悬念式、干货式、共鸣式、提问式四类（每类至少 2 个）；
2. 前 3 个标题必须有强点击欲；避免'震惊体'同质化套路；
3. 单条标题 ≤ 30 字；
4. 同时给出分层标签：3 个热门泛标签（大流量）+ 3 个行业中标签（精准触达）+ 6 个长尾标签（搜索流量），带#前缀。

{_TITLE_SCHEMA_HINT}"""
    return LLMSpec(
        task="titles", system=system, prompt=prompt, json_mode=True,
        temperature=settings.LLM_TEMPERATURE, max_tokens=settings.LLM_MAX_TOKENS,
        meta={"topic": topic, "platform": platform, "action": action,
              "existing_titles": existing_titles or []},
    )


def build_copywriting_spec(
    text: str, action: str, style: str, custom_style: str = ""
) -> LLMSpec:
    action_map = {
        "rewrite": "智能润色改写：保留原意，重塑表达，消除套话与冗余",
        "expand": "扩写丰富：在原文基础上扩充细节、案例与情绪层次，篇幅增加约 40%",
        "condense": "缩写精简：压缩至原篇幅 50% 以内，保留核心信息，句句有信息量",
        "style_transfer": "风格迁移：在保持信息完整的前提下重写为指定风格",
        "polish": "深度润色：替换平淡词汇、优化语序、增强节奏与画面感",
        "proofread": "纠错校对：修正错别字、病句与标点，不改动原有风格",
        "dedupe": "原创度提升：调整句式结构、更换同义词、打乱表达顺序，让文本焕然一新",
    }
    desc = action_map.get(action, action_map["rewrite"])
    style_note = STYLE_PROFILES.get(style, STYLE_PROFILES["通用"])["hint"]
    if custom_style:
        style_note = f"风格要求（自定义）：{custom_style}"

    system = (
        "你是一线新媒体公司的资深文案主编，精通小红书/抖音/电商全场景文案表达，"
        "擅长在保留信息量的前提下完成风格化重写，文风自然、有记忆点、可直接发布。"
        f"当前风格定位：{style_note}"
    )
    prompt = f"""任务：对下方原文进行「{desc}」。

【原文】
{text}

【输出要求】
1. result 为最终成稿正文，必须完整、可直接发布使用；
2. key_points 输出 2-4 条本次改写亮点（每条 ≤ 20 字）；
3. changed_count 用 0-100 量化与原稿的差异度；
4. 严守当前风格定位，不出现与风格冲突的措辞。

【输出 JSON 结构】
{{"result": "成稿正文", "key_points": ["亮点1","亮点2"], "changed_count": 60}}"""
    return LLMSpec(
        task="copywriting", system=system, prompt=prompt, json_mode=True,
        temperature=settings.LLM_TEMPERATURE, max_tokens=max(2048, min(4096, len(text) * 4)),
        meta={"text": text[:2000], "action": action, "style": style},
    )
