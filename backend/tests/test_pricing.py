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
