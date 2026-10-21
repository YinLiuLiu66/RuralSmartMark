import asyncio

from ..models import Batch, ProductProfile
from .base import AgentName


async def run_mock_agent(agent: AgentName, product: ProductProfile, batch: Batch) -> dict:
    """Deterministic demo output; replaced by real agents in Phase 2."""
    await asyncio.sleep(0.15)

    if agent == AgentName.STORY:
        return {
            "ip_name": "乌蒙丑丑",
            "persona": "住在乌蒙山腰的丑苹果守护者，说话慢、爱用山里的比喻，不卖惨。",
            "story_long": (
                f"{product.county}的秋天来得早。海拔约 1950m 的果园里，苹果不套袋，"
                "让太阳把表皮晒出斑点。它长得不漂亮，但把糖分留在了果肉里。"
                "这批果子由合作社分级、装箱，准备以“丑得真实，甜得直接”的名字走出大山。"
                "（演示稿，事实待核验）"
            ),
            "story_short": "长得丑，甜得认真。",
            "taglines": ["丑得真实，甜得直接", "不套袋的乌蒙丑苹果"],
            "cultural_evidence": [
                {
                    "doc_id": "ENV-01",
                    "quote": "海拔约 1800–2500m，核心坝区约 1950m（待核验）",
                    "use": "产地背景",
                }
            ],
            "tone_guide": "短句、具体、少形容词；不编人物姓名与亲历。",
            "demo": True,
        }

    if agent == AgentName.PACKAGING:
        return {
            "concept": "牛皮纸礼盒 · 把“丑”印在封面上",
            "palette": ["#B6402A", "#C9A46A", "#3F6B4F", "#F7F3EA"],
            "typography": "标题用宋体，正文用黑体；“丑”字放大做压纹。",
            "ip_image_prompt": "低多边形插画，乌蒙山苹果园，一个披斗篷的丑苹果守护者，暖色纸感。",
            "packaging_copy": {
                "front": "丑得真实，甜得直接",
                "back": "来自昭通昭阳区，海拔约 1950m 的苹果园。",
                "side": "5kg · 12 枚 · 80–85mm",
                "inside": "长得丑，是它认真晒太阳的证据。",
            },
            "structure": {
                "box_type": "牛皮纸天地盖礼盒",
                "dimensions": "360×260×90mm",
                "material": "350g 牛皮纸 + 瓦楞内托",
            },
            "cost_estimate": {"box": 3.2, "tray": 1.1, "print": 1.4, "total": 5.7, "currency": "CNY"},
            "derivative_ideas": ["苹果形状冰箱贴", "方言帆布袋"],
            "demo": True,
        }

    if agent == AgentName.MARKETING:
        return {
            "xiaohongshu": {
                "title": "长得丑，但它是真的甜",
                "body": "昭通丑苹果，不套袋、不抛光。表皮有斑点，切开是脆甜的果肉。5kg 礼盒，12 枚 80–85mm 大果。",
                "tags": ["#昭通丑苹果", "#助农", "#丑苹果"],
                "cover_text": "丑得真实",
            },
            "douyin": {
                "hook": "先别划走，这颗苹果长得有点丑。",
                "script": "镜头从果园开始，切开一颗丑苹果，最后落在牛皮纸礼盒上。",
                "shots": ["果园特写", "切开果肉", "礼盒开箱"],
            },
            "wechat": {
                "title": "一箱来自乌蒙山的丑苹果",
                "body": "不靠颜值，靠产地和分级。合作社直发，5kg 礼盒装。",
            },
            "cs_qa": [
                {"q": "为什么比别家贵？", "a": "贵在产地、分级和礼盒，不在“颜值”。"},
                {"q": "为什么表皮有斑点？", "a": "不套袋、不抛光，自然生长留下的痕迹。"},
            ],
            "kol_brief": {
                "profile": "云南本地美食博主",
                "rationale": "地域贴合，适合讲产地故事。",
                "message": "邀请你试吃一箱乌蒙丑苹果，重点拍“丑外表 + 甜果肉”的反差。",
                "deliverables": ["1 条短视频", "1 篇图文"],
            },
            "demo": True,
        }

    return {
        "price_ladder": [
            {"channel": "散装批发", "price": 10.0, "margin": 0.12},
            {"channel": "电商散装", "price": 12.0, "margin": 0.18},
            {"channel": "品牌礼盒", "price": 25.6, "margin": 0.35},
        ],
        "premium_pct": 156.0,
        "rationale": "以散装 10 元/kg 为基准，礼盒 25.6 元/kg，溢价 156%；演示测算。",
        "trace_timeline": [
            {"step": "采摘", "note": "昭阳区果园"},
            {"step": "分选", "note": "80–85mm"},
            {"step": "包装", "note": "牛皮纸礼盒"},
            {"step": "出库", "note": "演示批次"},
        ],
        "qr_payload": batch.trace_code or f"/trace/{batch.code}",
        "persona_greeting": "你好呀，我是乌蒙山的丑丑。",
        "faq": [
            {"q": "为什么叫丑苹果？", "a": "不套袋、不抛光，表皮有斑点。"},
            {"q": "怎么保存？", "a": "阴凉通风处，冷藏口感更脆。"},
        ],
        "demo": True,
    }
