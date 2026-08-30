# -*- coding: utf-8 -*-
"""TTS 配音专用文本生成（模块5 · 纯确定性规则引擎，零幻觉、零延迟）。

为什么用规则引擎而非 LLM：配音文本优化的诉求是"确定、可复现、不丢信息"，
LLM 有篡改原意风险；规则引擎 100% 保真，同时天然支持批量高并发。
规则集：
 1. 剥离画面标注（【旁白】【音乐】等）、字幕前缀（字幕：/画面：）、Markdown 符号；
 2. 长句智能断句：按句读切分，超长句在分句处二次切分，形成朗读停顿；
 3. 剔除书面连接词与口头填充词（综上所述/嗯/那个/就是说 等）；
 4. 净化冗余标点：省略号连用、重复停顿符、开头无意义语气词；
 5. 出镜/旁白模式识别：按首句人称与标注判断，匹配剪映剪辑场景。
"""
from __future__ import annotations

import re

from app.config import settings

# ---------- 剥离规则 ----------
_SKIP_PATTERNS = [
    re.compile(r"【[^】]{0,30}】"),            # 【音乐】【字幕】【旁白】
    re.compile(r"\([^)]{0,40}(音乐|音效|bmg|bgm|字幕|画面|镜头|转场|配音)[^)]{0,40}\)", re.I),  # (音乐起)
    re.compile(r"(字幕|画面|镜头|分镜|旁白|出镜|配音|音效)[：:]\s*"),   # 前缀标注
    re.compile(r"^[\s\d\.\-、:：]*"),           # 序号残留
]

_FILLERS = [
    re.compile(r"\b(嗯嗯?|呃+|啊+)\b"),
    re.compile(r"(这个这个|那个那个)+"),
    re.compile(r"(就是说|也就是说|然后呢|紧接着呢)+(?=[，。])"),
]

_CONNECTORS = ["综上所述", "总而言之", "换言之", "由此可见", "综上所述", "值得注意", "进一步来说", "首先其次"]

# ---------- 断句 ----------
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？…；])\s*|\n+")
_SECONDARY_SPLIT = re.compile(r"(?<=[，、：])")

# ---------- 净化 ----------
_MULTI_PUNCT = re.compile(r"([。！？…]{2,})")
_LEADING_FILLER = re.compile(r"^(嗯|呃|啊|唉|那个|然后|就是说)[，、]?")


def clean_text(raw: str) -> str:
    text = raw.strip()
    for pat in _SKIP_PATTERNS:
        text = pat.sub("", text)
    text = text.replace("```", "").replace("**", "").replace("#", "").replace("---", "")
    text = text.strip("，。；、：！？ ")
    return text


def split_sentences(text: str) -> list[str]:
    """一级切分（句读）-> 二级切分（超长句在分句处断），形成可控节奏。"""
    sentences: list[str] = []
    for piece in _SENTENCE_SPLIT.split(text):
        piece = piece.strip()
        if not piece:
            continue
        if len(piece) > settings.TTS_MAX_SENTENCE_LEN:
            # 在顿号/逗号处二次切分，每段不超过阈值
            parts, current = [], ""
            for token in _SECONDARY_SPLIT.split(piece):
                current = (current + token).strip()
                if len(current) >= settings.TTS_MAX_SENTENCE_LEN:
                    parts.append(current)
                    current = ""
            if current:
                parts.append(current)
            sentences.extend(p for p in parts if p)
        else:
            sentences.append(piece)
    return sentences


def detox(sentence: str) -> str:
    """单句净化：填充词、书面连接词、冗余标点、句首语气词。"""
    s = sentence
    for pat in _FILLERS:
        s = pat.sub("", s)
    for cw in _CONNECTORS:
        s = s.replace(cw, "")
    s = _LEADING_FILLER.sub("", s)
    s = _MULTI_PUNCT.sub(lambda m: m.group(1)[0], s)
    s = re.sub(r"[，、]{2,}", "，", s)
    s = re.sub(r"[ ]{2,}", " ", s)
    s = re.sub(r"[，,。]?$", "。", s) if s and not re.search(r"[。！？…]$", s) else s
    return s.strip()


def detect_mode(text: str) -> str:
    """on_camera=出镜口播 / narration=旁白配音。"""
    head = text[:100]
    if re.search(r"【(口播|出镜)|大家好|姐妹们|家人们|朋友们|老铁|各位", head):
        return "on_camera"
    return "narration"


def optimize(raw_text: str) -> dict:
    """入口：任意文本 -> 可直接复制进剪映的纯净口播稿。"""
    cleaned = clean_text(raw_text)
    raw_sentences = split_sentences(cleaned)
    sentences = [d for d in (detox(s) for s in raw_sentences) if d]

    text = "\n".join(sentences)
    if not sentences:
        return {
            "text": "", "sentences": [], "mode": "narration",
            "total_chars": 0, "est_duration_sec": 0,
            "removed_notes": True,
        }
    # 语速基准 4.2 字/秒（常规口播），估算成片朗读时长
    est = round(len(text) / 4.2, 1)
    return {
        "text": text,
        "sentences": sentences,
        "mode": detect_mode(text),
        "total_chars": len(text),
        "est_duration_sec": est,
        "removed_notes": len(cleaned) < len(raw_text),
    }


def script_lines_to_tts(segments: list[dict]) -> dict:
    """脚本分镜 -> 配音稿：按时间顺序串接台词，段间自然停顿。"""
    raw = "\n".join(f"{s.get('lines', '')}" for s in segments if s.get("lines"))
    result = optimize(raw)
    result["segment_count"] = len(segments)
    return result
