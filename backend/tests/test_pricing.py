"""M6 溢价对照验收：公开读、三档演示测算、reset 幂等。"""

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from ruralsmartmark import db
from ruralsmartmark.app import app
from ruralsmartmark.models import PriceBenchmark
from ruralsmartmark.sim.engine import engine

client = TestClient(app)


async def _prepare() -> None:
    await engine.reset()


def test_pricing_public_demo_rows() -> None:
    asyncio.run(_prepare())
    resp = client.get("/api/pricing/benchmarks")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["sku_name"] == "麻江蓝莓文创礼盒"
    assert "演示测算" in data["note"]
    assert [item["channel"] for item in data["items"]] == [
        "批发市场",
        "电商散装",
        "礼盒直营",
    ]
    assert [item["bulk_price"] for item in data["items"]] == [36.0, 58.0, 72.0]

    for item in data["items"]:
        assert item["brand_price"] == 128.0
        expected = (item["brand_price"] - item["bulk_price"]) / item["bulk_price"]
        assert abs(item["premium_rate"] - expected) < 0.001


def test_pricing_idempotent_on_reset() -> None:
    asyncio.run(_prepare())
    asyncio.run(_prepare())

    async def count_rows() -> int:
        async with db.session_factory() as session:
            return (
                await session.scalar(
                    select(func.count()).select_from(PriceBenchmark)
                )
                or 0
            )

    assert asyncio.run(count_rows()) == 3
