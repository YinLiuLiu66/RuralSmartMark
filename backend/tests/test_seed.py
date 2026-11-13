from ruralsmartmark.seed import PRODUCT_SLUG, seed_demo


async def test_seed_is_idempotent(session, client):
    first = await seed_demo(session)
    second = await seed_demo(session)

    assert first == {"products": 2, "batches": 3}
    assert second == first

    products = await client.get("/api/products")
    assert products.status_code == 200
    assert {item["slug"] for item in products.json()} == {
        PRODUCT_SLUG,
        "majiang-blueberry-demo",
    }

    batches = await client.get("/api/batches")
    assert batches.status_code == 200
    assert len(batches.json()) == 3
    assert {batch["code"] for batch in batches.json()} == {
        "ZT-DEMO-001",
        "ZT-2026-001",
        "MJ-2026-001",
    }

    demo = next(batch for batch in batches.json() if batch["code"] == "ZT-DEMO-001")
    workspace = (await client.get(f"/api/batches/{demo['id']}/workspace")).json()
    assert len(workspace["runs"]) == 4
    assert len(workspace["artifacts"]) == 4
    assert {artifact["kind"] for artifact in workspace["artifacts"]} == {
        "story",
        "packaging",
        "marketing",
        "pricing",
    }
