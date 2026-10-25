import json
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from ruralsmartmark.agents.schemas import PricingOutput
from ruralsmartmark.models import Batch, Benchmark, ProductProfile
from ruralsmartmark.seed import seed_demo
from ruralsmartmark.services.knowledge import list_knowledge_docs
from ruralsmartmark.services.pricing import PricingError, calculate_pricing


async def _context(session):
    await seed_demo(session)
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == "zhaotong-ugly-apple")
    )
    batch = await session.scalar(select(Batch).where(Batch.code == "ZT-2026-001"))
    benchmarks = list(
        (await session.execute(select(Benchmark).where(Benchmark.product_id == product.id)))
        .scalars()
        .all()
    )
    docs = await list_knowledge_docs(session, product.id)
    return product, batch, benchmarks, docs


async def test_pricing_is_deterministic(session):
    product, batch, benchmarks, docs = await _context(session)

    result = calculate_pricing(
        product,
        batch,
        {"cost_estimate": {"total": 5.7}},
        benchmarks,
        docs,
        public_base_url="http://127.0.0.1:5173",
    )

    assert result["premium_pct"] == 156.0
    assert result["price_ladder"][0]["price_total"] == 50.0
    assert result["price_ladder"][2]["price_total"] == 128.0
    assert result["price_ladder"][2]["price_per_kg"] == 25.6
    assert 0.4 < result["price_ladder"][2]["margin"] < 0.45
    assert "156.0%" in result["formula"]
    assert "演示测算" in result["rationale"]
    assert result["qr_payload"].endswith(f"/trace/{batch.code}")
    assert sum(result["cost_breakdown"].values()) == pytest.approx(
        result["price_ladder"][2]["price_per_kg"] * (1 - result["price_ladder"][2]["margin"]),
        abs=0.02,
    )

    validated = PricingOutput.model_validate(result)
    assert validated.is_demo


async def test_pricing_rejects_negative_gift_margin(session):
    product, batch, benchmarks, docs = await _context(session)
    for item in benchmarks:
        if item.channel == "品牌礼盒":
            item.price_per_kg = 12.0

    with pytest.raises(PricingError):
        calculate_pricing(
            product,
            batch,
            {"cost_estimate": {"total": 5.7}},
            benchmarks,
            docs,
            public_base_url="http://127.0.0.1:5173",
        )


def _bare_context(slug: str, name: str, specs: dict):
    product = SimpleNamespace(
        slug=slug,
        name=name,
        county="某某县",
        form="1kg / 箱",
        specs=specs,
    )
    batch = SimpleNamespace(code="XX-2026-001", quantity_kg=100.0)
    benchmarks = [
        SimpleNamespace(channel="散装批发", price_per_kg=10.0),
        SimpleNamespace(channel="电商散装", price_per_kg=12.0),
        SimpleNamespace(channel="品牌礼盒", price_per_kg=25.6),
    ]
    docs = [
        SimpleNamespace(doc_key="PRICE-01", content="演示测算采用散装批发 10 元/kg。"),
        SimpleNamespace(doc_key="DEMO-01", content="所有价格、成本和溢价均为演示测算。"),
    ]
    return product, batch, benchmarks, docs


def test_non_zhaotong_pricing_has_no_zhaotong_defaults():
    product, batch, benchmarks, docs = _bare_context("qingti", "青提", {})

    result = calculate_pricing(
        product,
        batch,
        {"cost_estimate": {"total": 5.7}},
        benchmarks,
        docs,
        public_base_url="http://127.0.0.1:5173",
    )

    serialized = json.dumps(result, ensure_ascii=False)
    for forbidden in ("80–85", "12 枚", "牛皮纸天地盖", "乌蒙山", "不套袋", "苹果"):
        assert forbidden not in serialized
    assert result["price_ladder"][0]["pack"] == "5kg / 箱"
    assert result["price_ladder"][2]["pack"] == "5kg / 箱"
    assert "按青提外观与规格分级" in result["trace_timeline"][1]["note"]
    assert result["trace_timeline"][2]["note"] == "5kg / 箱 包装（演示规格）"
    assert result["persona_greeting"].startswith("你好呀，我是青提记录者。")
    assert "这一批青提从某某县出发" in result["persona_greeting"]
    assert all("斑点" not in item["q"] for item in result["faq"])


def test_zhaotong_pricing_keeps_tuned_defaults():
    product, batch, benchmarks, docs = _bare_context("zhaotong-ugly-apple", "昭通丑苹果", {})

    result = calculate_pricing(
        product,
        batch,
        {"cost_estimate": {"total": 5.7}},
        benchmarks,
        docs,
        public_base_url="http://127.0.0.1:5173",
    )

    serialized = json.dumps(result, ensure_ascii=False)
    assert result["price_ladder"][2]["pack"] == "5kg / 12 枚"
    assert "80–85mm" in serialized
    assert "牛皮纸天地盖礼盒" in serialized
    assert "乌蒙山" in result["persona_greeting"]
    assert result["persona_greeting"].startswith("你好呀，我是山风守园人。")
