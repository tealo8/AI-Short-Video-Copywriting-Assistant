# -*- coding: utf-8 -*-
"""Mock Provider：无模型环境下的演示兜底。

当 Ollama 与云端均不可用时，返回构造良好的演示数据，
保证产品全流程可演示；响应中 source_model="mock" 由前端明确标注。
所有 mock 数据严格对齐真实 Schema，字段零缺失。
"""
from __future__ import annotations

import json
import random

from app.core.logging import get_logger
from app.services.llm.base import LLMProvider, LLMSpec

logger = get_logger("llm.mock")

STYLE_HINTS = {
    "小红书温柔种草风": "姐妹们，真的挖到宝了！",
    "抖音口播干货风": "今天这条视频，全是干货。",
    "正式专业科普风": "以下内容基于权威资料整理。",
    "幽默轻松段子风": "说出来你可能不信，这事吧——",
    "电商带货营销风": "家人们注意了，今天这个福利不抢真亏。",
    "极简高级短句风": "少即是多。",
}


class MockProvider(LLMProvider):
    name = "mock"

    # ---------------- 脚本 ----------------
    def _script(self, spec: LLMSpec) -> str:
        m = spec.meta
        topic = m.get("topic", "人工智能")
        platform = m.get("platform", "douyin")
        duration = int(m.get("duration", 60))
        style = m.get("style", "通用")

        seg_count = max(3, min(6, duration // 15))
        seg_len = duration // seg_count
        remainder = duration % seg_count

        lines_pool = [
            f"很多人不知道，{topic}里藏着三个反常识的细节，今天一条视频给你讲透。",
            f"先说结论：{topic}这件事，第一步就做错的人占八成。",
            "接下来拆解下一个关键点，建议先收藏再往下看。",
            "最后一步最容易被忽略，但我们实测下来效果差了三倍。",
        ]
        # 分段时长序列先行计算，再以 enumerate 遍历生成：
        # 索引变量 i 由 enumerate 提供，任何执行路径都一定有初始值，杜绝 UnboundLocalError。
        seg_durations = [
            seg_len + (1 if k < remainder else 0) for k in range(seg_count)
        ]
        segments, cursor = [], 0
        for i, seg_sec in enumerate(seg_durations):
            start = cursor
            end = cursor + seg_sec
            cursor = end
            segments.append({
                "index": i + 1,
                "start_time": self._fmt(start),
                "end_time": self._fmt(end),
                "duration_sec": seg_sec,
                "type": "on_camera" if i % 2 == 0 else "narration",
                "scene": (
                    f"画面：{topic}相关实拍/素材快切，突出关键词 {topic[:12]}；"
                    "字幕贴实时弹出，节奏跟随口播。"
                ),
                "lines": lines_pool[i % len(lines_pool)],
                "subtitle": f"{topic[:8]}·关键点{i + 1}",
            })

        titles = [
            {"title": f"{topic}是什么？90%的人第一步就错了", "tone": "提问式"},
            {"title": f"花3分钟搞懂{topic}，你的效率翻倍", "tone": "干货式"},
            {"title": f"做{topic}前，我真后悔没早点看到这条", "tone": "共鸣式"},
            {"title": f"关于{topic}，我想说点大家不敢说的", "tone": "悬念式"},
            {"title": f"{topic}避坑指南｜看完少走三年弯路", "tone": "干货式"},
            {"title": f"如果你是新手，{topic}请这样入门", "tone": "共鸣式"},
            {"title": f"为什么聪明人都在悄悄学{topic}？", "tone": "悬念式"},
            {"title": f"{topic}从0到1，一条视频讲清楚", "tone": "干货式"},
            {"title": f"别再瞎试了！{topic}的正确打开方式", "tone": "悬念式"},
            {"title": f"分享一个{topic}的万能公式，建议收藏", "tone": "干货式"},
        ]
        tags = {
            "hot": ["#热门", "#涨知识", "#干货分享"][:3],
            "mid": [f"#{topic}", "#短视频创作", "#自媒体"][:3],
            "long": [f"#{topic}教程", f"#{topic}入门", f"#{topic}避坑", "#新手友好", "#内容创作", "#流量密码"],
        }
        data = {
            "topic_overview": f"以{topic}为主题，适配{platform}平台的{duration}秒结构化口播脚本，"
                              f"风格：{style}。开头设钩、中段拆解、结尾互动，全片节奏紧凑。",
            "hook": f"开局一句话：{topic}这事，你以前的理解可能全错了。",
            "segments": segments,
            "ending": f"如果这条视频对你有帮助，点赞收藏；评论区聊聊你与{topic}的故事，下期拆解更多干货。",
            "titles": titles,
            "tags": tags,
        }
        return json.dumps(data, ensure_ascii=False)

    # ---------------- 标题标签 ----------------
    def _titles(self, spec: LLMSpec) -> str:
        m = spec.meta
        topic = m.get("topic", "人工智能")
        existing = m.get("existing_titles") or []
        if existing and m.get("action") == "polish":
            data = {
                "titles": [
                    {"title": f"{t.strip()}（升级版）", "tone": "强化"}
                    for t in existing[:10]
                ],
                "tags": {"hot": ["#热门", "#上热门"], "mid": [f"#{topic}"], "long": [f"#{topic}进阶"]},
            }
            return json.dumps(data, ensure_ascii=False)
        data = {
            "titles": [
                {"title": f"{topic}为什么突然火了？一个视频看懂", "tone": "悬念式"},
                {"title": f"3分钟讲透{topic}，建议反复观看", "tone": "干货式"},
                {"title": f"被{topic}折磨过的人，都懂这段话", "tone": "共鸣式"},
                {"title": f"{topic}适合普通人吗？我的真实答案", "tone": "提问式"},
                {"title": f"新手做{topic}，只犯这三个错就够了", "tone": "干货式"},
                {"title": f"这件事我整整准备了30天：{topic}复盘", "tone": "共鸣式"},
                {"title": f"没人告诉你的{topic}真相，全在这7分钟", "tone": "悬念式"},
                {"title": f"{topic}从入门到进阶，一篇讲完", "tone": "干货式"},
                {"title": f"你还不知道{topic}还能这么玩？", "tone": "提问式"},
                {"title": f"刷到就是缘分：{topic}的3个隐藏用法", "tone": "悬念式"},
            ],
            "tags": {
                "hot": ["#热门", "#知识分享", "#上热门"],
                "mid": [f"#{topic}", "#短视频", "#自媒体"][:3],
                "long": [f"#{topic}攻略", f"#{topic}教程", "#新手入门", "#干货分享", "#涨知识", "#效率工具"],
            },
        }
        return json.dumps(data, ensure_ascii=False)

    # ---------------- 文案改写 ----------------
    def _copywriting(self, spec: LLMSpec) -> str:
        m = spec.meta
        text = m.get("text", "原始文案内容")
        action = m.get("action", "rewrite")
        style = m.get("style", "通用")
        hint = STYLE_HINTS.get(style, f"【{style}】")
        action_desc = {
            "rewrite": "在保留原意的前提下重塑表达，消除套话",
            "expand": "在原文基础上扩充细节、案例与情绪层次，篇幅增加40%",
            "condense": "压缩至原篇幅50%以内，保留核心信息，句句有信息量",
            "style_transfer": f"迁移为「{style}」语言风格",
            "polish": "润色增色：替换平淡词汇、优化语序、增强节奏",
            "proofread": "纠错：修正错别字、语病、标点，不动文风",
            "dedupe": "原创度提升：调整句式结构、更换同义词、打乱表达顺序",
        }.get(action, "按需求优化")
        result = (
            f"{hint}\n\n"
            f"{action_desc}完成版：\n\n"
            f"「{text.strip()[:60]}」——围绕这句话，我们换一个更有记忆点的讲法：\n"
            f"第一，把结论前置，先给结果再给过程；"
            f"第二，用具体数字和场景替代抽象描述；"
            f"第三，结尾留一个互动钩子。以下为改写后正文：\n\n"
            f"{text.strip()}\n\n（Mock 演示模式：接入 Ollama/云端模型后这里将输出真实的风格化改写结果。）"
        )
        return json.dumps({
            "result": result,
            "key_points": ["结论前置，观点先行", "场景具体化", "结尾设置互动钩子"],
            "changed_count": 12,
        }, ensure_ascii=False)

    # ---------------- 入口 ----------------
    def generate(self, spec: LLMSpec) -> str:
        if spec.task == "script":
            return self._script(spec)
        if spec.task == "titles":
            return self._titles(spec)
        if spec.task == "copywriting":
            return self._copywriting(spec)
        # 兜底：无论什么任务都返回合法 JSON
        return json.dumps({"result": "（Mock 演示数据）", "key_points": []}, ensure_ascii=False)

    def health(self) -> dict:
        return {"ok": True, "detail": "Mock 演示数据模式已启用（真实模型不可达时自动兜底）"}

    @staticmethod
    def _fmt(seconds: int) -> str:
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
