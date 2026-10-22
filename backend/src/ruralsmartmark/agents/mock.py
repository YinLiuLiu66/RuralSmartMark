from __future__ import annotations

import asyncio
from typing import Any

from ..models import Batch, Benchmark, KnowledgeDoc, ProductProfile
from ..services.knowledge import quote_containing
from ..services.pricing import calculate_pricing
from .base import AgentName


def _doc(docs: list[KnowledgeDoc], doc_id: str) -> KnowledgeDoc:
    for doc in docs:
        if doc.doc_key == doc_id:
            return doc
    raise ValueError(f"知识库缺少 {doc_id}，无法生成 mock 产出")


def _quote(docs: list[KnowledgeDoc], doc_id: str, needle: str) -> dict[str, str]:
    return {
        "doc_id": doc_id,
        "quote": quote_containing(_doc(docs, doc_id), needle),
        "use": "演示引用",
    }


async def run_mock_agent(
    agent: AgentName,
    product: ProductProfile,
    batch: Batch,
    docs: list[KnowledgeDoc],
    benchmarks: list[Benchmark],
    *,
    packaging: dict[str, Any] | None = None,
    public_base_url: str = "http://127.0.0.1:5173",
) -> dict[str, Any]:
    """Deterministic demo output used by tests and as a provider fallback."""
    await asyncio.sleep(0.05)

    if agent == AgentName.STORY:
        return {
            "ip_name": "山风守园人",
            "persona": (
                "把乌蒙山风拟人化的守园人，演示合成的角色；说话慢、爱用山里的比喻，不卖惨；"
                "遇到不确定的事会先问“这是哪块地里的？”。"
            ),
            "story_long": (
                "乌蒙山里的秋天来得早。果园里的苹果不套袋，任凭太阳把表皮晒出斑点，"
                "也把糖分慢慢留在果肉里。它们长得不漂亮，却各有各的样子：有的歪一点，"
                "有的红得深一点，有的还带着一片叶子的影子。合作社把果子按大小分开，"
                "一箱一箱装箱，准备让它们以“乌蒙丑果”的名字走出大山。"
                "这里的高海拔、长日照和昼夜温差，是苹果慢慢长甜的条件；"
                "但冰糖心不是每一颗都有，我们不把偶然说成保证。"
                "这批果子从果园到分选台，再到礼盒和溯源码，每一步都留下记录。"
                "合作社把每一箱的重量、果径和采摘日期记在本子上，也把当天说过的笑话记在边上；"
                "这些记录后来变成一张小小的溯源码，贴在礼盒侧面。"
                "你看到的斑点，是它认真晒过太阳的证据；你尝到的脆甜，"
                "是这片山地和这一季雨水一起写下的答案。"
            ),
            "story_short": "长得丑，甜得认真。",
            "taglines": ["丑得真实，甜得直接", "不套袋的乌蒙丑苹果", "把山野装进礼盒"],
            "cultural_evidence": [
                _quote(docs, "ENV-02", "低纬度、高海拔"),
                _quote(docs, "GI-01", "2010年11月15日"),
                _quote(docs, "DEMO-01", "本项目的合作社"),
            ],
            "tone_guide": "短句、具体、少形容词；不编人物姓名、亲历和传说；不确定的数字不写。",
            "demo": True,
            "fallback_reason": None,
        }

    if agent == AgentName.PACKAGING:
        return {
            "concept": "牛皮纸礼盒 · 把“丑”印在封面上",
            "palette": ["#B6402A", "#C9A46A", "#3F6B4F", "#F7F3EA"],
            "typography": "标题用宋体，正文用黑体；“丑”字放大做压纹，保留纸张手感。",
            "ip_image_prompt": (
                "低多边形插画，乌蒙山苹果园，一个披斗篷的丑苹果守护者，暖色纸感，"
                "牛皮纸礼盒，苹果红与叶绿，平面印刷风。"
            ),
            "packaging_copy": {
                "front": "丑得真实，甜得直接",
                "back": "来自昭通昭阳区的高海拔果园；不套袋管理（演示设定）。",
                "side": "5kg · 12 枚 · 80–85mm",
                "inside": "长得丑，是它认真晒太阳的证据。",
            },
            "structure": {
                "box_type": "牛皮纸天地盖礼盒",
                "dimensions": "360×260×90mm",
                "material": "350g 牛皮纸 + 瓦楞内托",
            },
            "cost_estimate": {
                "box": 3.2,
                "tray": 1.1,
                "print": 1.4,
                "total": 5.7,
                "currency": "CNY",
            },
            "derivative_ideas": ["苹果形状冰箱贴", "方言帆布袋", "批次故事卡"],
            "fact_refs": [
                _quote(docs, "PACK-01", "演示包装规格"),
                _quote(docs, "DEMO-01", "不套袋、不打蜡"),
            ],
            "demo": True,
            "fallback_reason": None,
        }

    if agent == AgentName.MARKETING:
        return {
            "xiaohongshu": {
                "title": "长得丑，但它是真的甜",
                "body": (
                    "昭通昭阳区的丑苹果，不套袋、不抛光（演示合作社设定）。"
                    "表皮有斑点，切开是脆甜的果肉。5kg 礼盒，12 枚 80–85mm 大果，"
                    "每一箱都有批次故事和溯源码。"
                ),
                "tags": ["#昭通丑苹果", "#助农", "#丑苹果", "#山野好物"],
                "cover_text": "丑得真实",
            },
            "douyin": {
                "hook": "先别划走，这颗苹果长得有点丑。",
                "script": (
                    "镜头从乌蒙山果园开始，掠过带斑点的果皮，切开一颗苹果，"
                    "果肉脆响；最后落在牛皮纸礼盒和溯源码上。"
                ),
                "shots": ["果园特写", "带斑点果皮", "切开果肉", "礼盒开箱", "扫码溯源"],
            },
            "wechat": {
                "title": "一箱来自乌蒙山的丑苹果",
                "body": (
                    "不靠颜值，靠产地、分级和记录。合作社直发，5kg 礼盒装，"
                    "12 枚 80–85mm 大果；外表的斑点不是瑕疵，是它晒过太阳的痕迹。"
                ),
            },
            "cs_qa": [
                {"q": "为什么比散装贵？", "a": "贵在分级、礼盒、内容与溯源服务；价格是演示测算。"},
                {"q": "为什么表皮有斑点？", "a": "演示合作社采用不套袋管理，外观不代表果肉品质。"},
                {"q": "怎么保存？", "a": "阴凉通风处保存，冷藏口感更脆。"},
            ],
            "kol_brief": {
                "profile": "云南本地美食博主",
                "rationale": "地域贴合，适合讲产地与“丑外表 + 甜果肉”的反差。",
                "message": "邀请试吃一箱乌蒙丑果，重点拍果皮斑点、切开果肉和礼盒开箱。",
                "deliverables": ["1 条短视频", "1 篇图文"],
            },
            "fact_refs": [
                _quote(docs, "DEMO-01", "不套袋、不打蜡"),
                _quote(docs, "CUL-01", "藏在乌蒙山里"),
            ],
            "demo": True,
            "fallback_reason": None,
        }

    if packaging is None:
        packaging = {"cost_estimate": {"total": 5.7}}
    output = calculate_pricing(
        product,
        batch,
        packaging,
        benchmarks,
        docs,
        public_base_url=public_base_url,
        story={"ip_name": "山风守园人"},
        trace_code=batch.trace_code,
    )
    output["demo"] = True
    return output
