import json
from pathlib import Path

from ruralsmartmark.models import Batch, Benchmark, ProductProfile
from ruralsmartmark.services.knowledge import upsert_knowledge_docs

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "majiang"
AGENTS = ["story", "packaging", "marketing", "pricing"]


async def _seed_majiang(session) -> tuple[ProductProfile, Batch]:
    data = json.loads((FIXTURE_DIR / "product.json").read_text(encoding="utf-8"))
    knowledge_dir = FIXTURE_DIR / "knowledge"
    product = ProductProfile(
        slug=data["slug"],
        name=data["name"],
        county=data["county"],
        province=data["province"],
        category=data["category"],
        form=data["form"],
        specs=data["specs"],
        palette=data["palette"],
        scene_preset=data["scene_preset"],
        knowledge_dir=str(knowledge_dir),
        is_active=True,
    )
    session.add(product)
    await session.flush()
    await upsert_knowledge_docs(session, product.id, product.knowledge_dir)

    for channel, price in (("散装批发", 22.0), ("电商散装", 30.0), ("品牌礼盒", 60.0)):
        session.add(
            Benchmark(
                product_id=product.id,
                channel=channel,
                competitor="第二产品夹具",
                spec="2kg/箱",
                price_per_kg=price,
                source_url="https://example.com/ruralsmartmark/majiang-fixture",
                source_date="2026-10-22",
                note="夹具价格，仅用于测试",
            )
        )

    batch = Batch(
        product_id=product.id,
        code="MJ-TEST-001",
        quantity_kg=120.0,
        state="raw",
        current_station="intake",
    )
    session.add(batch)
    await session.commit()
    await session.refresh(batch)
    return product, batch


async def test_second_product_runs_without_code_changes(session, client):
    product, batch = await _seed_majiang(session)

    workspace = None
    for agent in AGENTS:
        started = await client.post(f"/api/batches/{batch.id}/pipeline/start")
        assert started.status_code == 200, started.text
        approved = await client.post(
            f"/api/batches/{batch.id}/agents/{agent}/approve",
            json={},
        )
        assert approved.status_code == 200, approved.text
        workspace = approved.json()

    assert workspace is not None
    assert workspace["batch"]["state"] == "traced"
    trace_code = workspace["batch"]["trace_code"]
    assert trace_code == f"MJ{batch.id:04d}"
    assert len(workspace["runs"]) == 4
    assert {artifact["kind"] for artifact in workspace["artifacts"]} == {
        "story",
        "packaging",
        "marketing",
        "pricing",
    }

    trace = (await client.get(f"/api/trace/{trace_code}")).json()
    assert trace["product"]["name"] == "麻江蓝莓"
    assert trace["product"]["brand_name"] == "雾岭蓝"
    assert trace["story"]["ip_name"] == "雾岭守莓人"
    assert trace["story"]["story_short"] == "雾里长，酸得清亮。"
    assert trace["pricing"]["premium_pct"] == 172.7
    assert trace["pricing"]["price_ladder"][2]["pack"] == "1.5kg / 6 盒"
    assert trace["packaging"]["packaging_copy"]["side"].startswith("1.5kg")

    serialized = json.dumps(trace, ensure_ascii=False)
    for forbidden in ("昭通", "乌蒙", "山风", "苹果"):
        assert forbidden not in serialized

    packaging_png = await client.get(f"/api/trace/{trace_code}/packaging.png")
    assert packaging_png.status_code == 200
    assert packaging_png.content.startswith(b"\x89PNG")
    assert product.slug == "majiang-blueberry"
