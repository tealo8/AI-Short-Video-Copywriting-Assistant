# -*- coding: utf-8 -*-
"""Prompt 模板库：平台画像 / 风格画像 / 输出守则 / 各任务 Prompt 骨架。

设计原则（分层可配置）：
- 平台、风格、时长、字数、结构全部抽为可配置变量，业务代码零硬编码；
- 模板即代码：新增平台/风格只需在此处登记一条画像，无需改服务逻辑。
"""
from __future__ import annotations

# ---------------- 平台画像层（LAYER 2-A） ----------------
PLATFORM_PROFILES: dict[str, dict] = {
    "douyin": {
        "label": "抖音",
        "traits": "强算法推荐、用户划走成本极低，前3秒必须直击痛点；口语化、节奏快、信息密度高；"
                  "完播率与互动率是核心指标；结尾引导关注/评论区互动。",
        "title_style": "悬念前置、数字冲击、制造反差；标题不超过30字。",
        "vibe": "接地气、快节奏、观点鲜明",
    },
    "xiaohongshu": {
        "label": "小红书",
        "traits": "搜索+推荐双分发，注重收藏与长尾搜索价值；标题可带 emoji 与关键词堆叠；"
                  "内容走'我就是亲身经历'的分享感，开篇给结论或反差。",
        "title_style": "关键词前置+情绪词，可用 emoji；字数 16-24 字。",
        "vibe": "真诚分享、细腻、有温度",
    },
    "shipinhao": {
        "label": "视频号",
        "traits": "社交推荐为主，熟人点赞驱动；内容偏理性、有价值感、正能量；"
                  "开头可做观点铺垫，结尾引导'转发给需要的人'。",
        "title_style": "稳重、价值导向，善用'建议收藏''转给家人'式文案。",
        "vibe": "理性、可靠、有深度",
    },
    "bilibili": {
        "label": "哔哩哔哩",
        "traits": "中长视频生态、用户耐心高，欢迎结构化的干货表达；弹幕文化强，"
                  "内容讲究逻辑链与信息增量。",
        "title_style": "明确告知内容价值，可带序号/盘点感词汇。",
        "vibe": "专业、有逻辑、可以稍微硬核",
    },
}

# ---------------- 风格画像层（LAYER 2-B） ----------------
STYLE_PROFILES: dict[str, dict] = {
    "通用": {"hint": "自然、清晰、口语化，观点明确，节奏明快。"},
    "小红书温柔种草风": {"hint": "第一人称'姐妹'式分享，真诚细腻；多用感叹与生活化比喻；"
                                "结尾制造'被种草的冲动'；句式可短可长，带情绪词。"},
    "抖音口播干货风": {"hint": "前3秒抛结论/痛点，逐条拆解，'记住了吗''划重点'式互动；"
                              "短句为主，动词开头，信息密度高。"},
    "正式专业科普风": {"hint": "术语准确、逻辑严谨、来源可靠；结论先行的总分结构；"
                              "避免绝对化措辞，可引用数据与原理。"},
    "幽默轻松段子风": {"hint": "梗化表达、自嘲与反转；加'说实话''笑死'等口语点缀；"
                              "贴近受众日常，结尾留包袱。"},
    "电商带货营销风": {"hint": "痛点-场景-解决方案-限时优惠结构；使用'家人们''直接说'等转化话术；"
                              "强调稀缺与行动指令（点击/拍下）。"},
    "极简高级短句风": {"hint": "句子极短、留白大、意象干净；删掉一切修饰与连接词；"
                              '单句不超过20字，少量短句成诗感。'},
}

# ---------------- 输出守则（LAYER 3 恒定约束） ----------------
_OUTPUT_RULES = """【输出守则 - 必须无条件遵守】
1. 只输出一个 JSON 对象，禁止任何解释文字、Markdown 围栏、前后缀说明；
2. 所有字段必须给出，不得省略、不得为 null；
3. 值中不要使用反问句填字段，内容要具体落地、可直接使用；
4. 台词使用自然口语，符合人声朗读节奏，避免书面化长句；
5. 时间格式 MM:SS 严格对应 duration_sec，全部镜头段时长之和必须等于视频总时长；
6. 标题不得重复，风格分布均匀且有差异；标签带#前缀，前后不加空格。"""


def _schema_hint() -> str:
    """给模型的 JSON 结构说明（与 pydantic Schema 保持镜像）。"""
    return """【输出 JSON 结构】
{
  "topic_overview": "主题概述(≤80字)",
  "hook": "开场3秒爆款钩子(≤40字)",
  "segments": [
    {
      "index": 1,
      "start_time": "00:00",
      "end_time": "00:10",
      "duration_sec": 10,
      "type": "on_camera(出镜口播) 或 narration(旁白)",
      "scene": "画面描述：景别/运镜/素材",
      "lines": "本段台词，口语化",
      "subtitle": "字幕重点(≤20字)"
    }
  ],
  "ending": "结尾互动引导(≤60字)",
  "titles": [{"title": "标题内容", "tone": "悬念式|干货式|共鸣式|提问式"}],
  "tags": {
    "hot": ["#泛标签","#泛标签","#泛标签"],
    "mid": ["#中标签","#中标签","#中标签"],
    "long": ["#长尾1","#长尾2","#长尾3","#长尾4","#长尾5","#长尾6"]
  }
}"""


def build_script_spec(
    topic: str, platform: str, duration: int, style: str, custom_style: str = "",
    word_budget: tuple[int | None, int | None] | None = None,
) -> tuple[str, str]:
    """脚本任务：返回 (system, prompt)。word_budget=(min,max) 字数范围约束。"""
    p = PLATFORM_PROFILES.get(platform, PLATFORM_PROFILES["douyin"])
    s = STYLE_PROFILES.get(style, STYLE_PROFILES["通用"])
    style_note = f"风格要求：{s['hint']}" if not custom_style else f"风格要求（自定义）：{custom_style}"

    # 字数预算：口播语速约 4 字/秒，台词总量 = 时长 × 4，钩子/结尾各留 20-30 字
    default_budget = int(duration * 4.0)
    if word_budget and (word_budget[0] or word_budget[1]):
        lo, hi = word_budget
        lo = lo or max(20, min(600, default_budget // 2))
        hi = hi or max(lo, min(1000, default_budget * 2))
        lo, hi = max(20, min(lo, hi)), max(lo, min(hi, 1000))
        budget_note = (
            f"【用户指定字数】台词总量必须控制在 {lo} 到 {hi} 字之间"
            f"（口播语速约 4 字/秒，{duration} 秒基准为 {default_budget} 字）"
        )
    else:
        budget_note = f"【字数预算】台词总量约 {default_budget} 字（正负15%），长短句结合，保证朗读节奏"
    seg_count = max(3, min(6, duration // 15))

    system = (
        "你是一位深耕短视频行业8年的资深编导与爆款文案操盘手，精通抖音/小红书/视频号/哔哩哔哩"
        "各平台算法逻辑与内容调性，擅长把主题拆解为可直接开拍的标准化分镜脚本。"
        "你的输出必须严格符合给定的 JSON 结构，内容质量对标百万粉博主水平。"
    )
    prompt = f"""请为以下需求创作一条完整短视频脚本套装。

【主题】{topic}
【目标平台】{p['label']}（算法特点：{p['traits']}）
【视频时长】{duration} 秒（总时长必须精确，所有分段时长之和必须等于 {duration} 秒）
【镜头数量】{seg_count} 段左右（可按内容微调，但不少于 3 段、不多于 6 段，每段 8-20 秒）
{budget_note}
【标题风格】{p['title_style']}
【整体调性】{p['vibe']}
{style_note}

【内容要求】
1. hook 必须 3 秒内抓住用户，符合 {p['label']} 用户心理，禁用陈词滥调；
2. segments 每段清晰：先给 scene（画面），再给 lines（台词），subtitle 提炼字幕重点；
3. 台词必须口语化、可直接对着镜头念，禁止写成书面文章；
4. ending 引导互动（点赞/收藏/评论/关注/转发，按 {p['label']} 生态选择 1-2 个动作）；
5. titles 给出 10 个完全差异化标题，覆盖悬念式/干货式/共鸣式/提问式四类，每类至少 2 个；
6. tags 共 12 个：3 个热门泛标签 + 3 个行业中标签 + 6 个精准长尾标签。

{_schema_hint()}

{_OUTPUT_RULES}"""
    return system, prompt
