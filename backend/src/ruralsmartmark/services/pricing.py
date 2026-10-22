from __future__ import annotations

from typing import Any

from ..models import Batch, Benchmark, KnowledgeDoc, ProductProfile
from .knowledge import quote_containing

PACK_KG = 5.0
BULK_PACK_KG = 5.0


class PricingError(ValueError):
    """定价基准或成本假设无法得到非负毛利。"""


def _price_of(benchmarks: list[Benchmark], channel: str, fallback: float) -> float:
    for item in benchmarks:
        if item.channel == channel:
            return float(item.price_per_kg)
    return fallback


def _round_money(value: float) -> float:
    return round(value + 1e-9, 2)


def _margin(price: float, cost: float) -> float:
    return round((price - cost) / price, 4) if price else 0.0


def calculate_pricing(
    product: ProductProfile,
    batch: Batch,
    packaging: dict[str, Any],
    benchmarks: list[Benchmark],
    docs: list[KnowledgeDoc],
    *,
    public_base_url: str,
    story: dict[str, Any] | None = None,
    trace_code: str | None = None,
) -> dict[str, Any]:
    specs = product.specs or {}
    bulk = _price_of(benchmarks, "散装批发", 10.0)
    ecommerce = _price_of(benchmarks, "电商散装", max(bulk * 1.2, bulk + 1))
    gift = _price_of(benchmarks, "品牌礼盒", max(ecommerce * 2, 25.6))

    cost = packaging.get("cost_estimate") or {}
    box_total = float(cost.get("total", 5.7))
    box_kg = float(specs.get("pack_kg", PACK_KG))
    bulk_kg = float(specs.get("bulk_pack_kg", BULK_PACK_KG))
    gift_pack = str(specs.get("gift_pack_label") or "5kg / 12 枚")
    ecommerce_pack = str(specs.get("ecommerce_pack_label") or gift_pack)
    bulk_pack = str(specs.get("bulk_pack_label") or "10 斤/箱")

    # 演示成本模型：果价 + 损耗 + 分选人工 + 冷链 + 包装 + 平台/营销费。
    fruit = bulk * 0.8
    loss = fruit * 0.04
    sorting = 1.0
    cold_chain = 1.2
    ecommerce_pack_cost = 0.4
    platform_rate = 0.05
    marketing_rate = 0.06

    bulk_cost = fruit + loss + sorting
    ecommerce_cost = (
        fruit + loss + sorting + cold_chain + ecommerce_pack_cost + ecommerce * platform_rate
    )
    gift_goods_cost = fruit + loss + sorting + cold_chain + box_total / box_kg
    gift_fees = gift * (platform_rate + marketing_rate)
    gift_cost = gift_goods_cost + gift_fees

    if gift_cost >= gift:
        raise PricingError(
            f"礼盒价 {gift:.2f} 元/kg 低于成本 {gift_cost:.2f} 元/kg，请调整基准价或成本假设"
        )

    gift_total = _round_money(gift * box_kg)
    ecommerce_total = _round_money(ecommerce * box_kg)
    bulk_total = _round_money(bulk * bulk_kg)
    premium = round((gift - bulk) / bulk * 100, 1) if bulk else 0.0
    gift_margin = _margin(gift, gift_cost)
    ecommerce_margin = _margin(ecommerce, ecommerce_cost)
    bulk_margin = _margin(bulk, bulk_cost)

    channel_rows = [
        {
            "channel": "散装批发",
            "pack": bulk_pack,
            "price_per_kg": _round_money(bulk),
            "price_total": bulk_total,
            "margin": bulk_margin,
            "note": "产地整箱、非礼盒；演示测算",
        },
        {
            "channel": "电商散装",
            "pack": ecommerce_pack,
            "price_per_kg": _round_money(ecommerce),
            "price_total": ecommerce_total,
            "margin": ecommerce_margin,
            "note": "电商发货、普通箱装；演示测算",
        },
        {
            "channel": "品牌礼盒",
            "pack": gift_pack,
            "price_per_kg": _round_money(gift),
            "price_total": gift_total,
            "margin": gift_margin,
            "note": "故事 + 包装 + 内容 + 溯源后的目标价；演示测算",
        },
    ]

    formula = (
        f"溢价率 = (品牌礼盒 {gift:.1f} 元/kg - 散装批发 {bulk:.1f} 元/kg) / "
        f"{bulk:.1f} × 100% = {premium:.1f}%；"
        f"礼盒毛利 = (售价 {gift:.1f} - 货品成本 {gift_goods_cost:.2f} - 平台/营销费 "
        f"{gift_fees:.2f}) / 售价 = {gift_margin * 100:.1f}%。"
    )

    rationale = (
        f"以散装批发 {bulk:.1f} 元/kg 为基线，{box_kg:g}kg 品牌礼盒定价 {gift_total:.1f} 元"
        f"（{gift:.1f} 元/kg），溢价 {premium:.1f}%；"
        f"礼盒货品成本约 {gift_goods_cost * box_kg:.2f} 元，平台/营销费约 "
        f"{gift_fees * box_kg:.2f} 元，净毛利约 {gift_margin * 100:.1f}%。"
        "以上为演示测算，不是市场报价或增收承诺。"
    )

    trace_url = f"{public_base_url.rstrip('/')}/trace/{trace_code or batch.code}"
    ip_name = (story or {}).get("ip_name") or "山风守园人"
    greeting_scene = str(
        specs.get("persona_greeting_scene")
        or "这颗苹果从乌蒙山出发，身上有太阳晒出的斑点，也有这一批合作社的分级和装箱记录。"
    )
    persona_greeting = f"你好呀，我是{ip_name}。{greeting_scene}"

    price_doc = next((doc for doc in docs if doc.doc_key == "PRICE-01"), None)
    demo_doc = next((doc for doc in docs if doc.doc_key == "DEMO-01"), None)
    if price_doc is None or demo_doc is None:
        raise PricingError("知识库缺少 PRICE-01 或 DEMO-01，无法生成可追溯定价")

    fact_refs = [
        {
            "doc_id": "PRICE-01",
            "quote": quote_containing(price_doc, "演示测算采用"),
            "use": "演示价格基线",
        },
        {
            "doc_id": "DEMO-01",
            "quote": quote_containing(demo_doc, "所有价格、成本和溢价均为演示测算"),
            "use": "演示测算边界",
        },
    ]

    faq = specs.get("pricing_faq")
    if not (
        isinstance(faq, list)
        and faq
        and all(isinstance(item, dict) and item.get("q") and item.get("a") for item in faq)
    ):
        faq = [
            {
                "q": "为什么比散装贵？",
                "a": "价格里包含分级、礼盒包装、内容制作与溯源服务；具体数字是演示测算。",
            },
            {
                "q": "表皮为什么有斑点？",
                "a": "演示合作社采用不套袋管理（演示设定），外观不代表果肉品质。",
            },
            {
                "q": "怎么保存？",
                "a": "阴凉通风处保存，冷藏口感更脆；建议按批次标注的时间尽快食用。",
            },
        ]

    return {
        "price_ladder": channel_rows,
        "premium_pct": premium,
        "rationale": rationale,
        "formula": formula,
        "cost_breakdown": {
            "果价": _round_money(fruit),
            "损耗": _round_money(loss),
            "分选人工": _round_money(sorting),
            "冷链": _round_money(cold_chain),
            "礼盒": _round_money(box_total / box_kg),
            "平台费": _round_money(gift * platform_rate),
            "营销费": _round_money(gift * marketing_rate),
        },
        "trace_timeline": [
            {"step": "采摘", "note": f"{product.county} · 演示批次 {batch.code}"},
            {
                "step": "分选",
                "note": str(specs.get("sorting_note") or "果径 80–85mm · 12 枚/盒（演示规格）"),
            },
            {
                "step": "包装",
                "note": str(
                    specs.get("packaging_note") or "牛皮纸天地盖礼盒 + 瓦楞纸托（演示规格）"
                ),
            },
            {"step": "定价", "note": f"散装基线 {bulk:.1f} 元/kg，礼盒目标 {gift:.1f} 元/kg"},
            {"step": "出库", "note": f"{batch.quantity_kg:g}kg 演示批次，冷链发运"},
            {"step": "扫码", "note": "消费者扫码查看批次故事、包装与定价说明"},
        ],
        "qr_payload": trace_url,
        "persona_greeting": persona_greeting,
        "faq": faq,
        "fact_refs": fact_refs,
        "is_demo": True,
        "narrative_source": "template",
        "demo": False,
        "fallback_reason": None,
    }
