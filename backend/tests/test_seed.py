from ruralsmartmark.seed import PRODUCT_SLUG, seed_demo


async def test_seed_is_idempotent(session, client):
    first = await seed_demo(session)
    second = await seed_demo(session)

    assert first == {"products": 1, "batches": 2}
    assert second == first

    products = await client.get("/api/products")
    assert products.status_code == 200
    assert products.json()[0]["slug"] == PRODUCT_SLUG

    batches = await client.get("/api/batches")
    assert batches.status_code == 200
    assert len(batches.json()) == 2
    assert {batch["code"] for batch in batches.json()} == {"ZT-DEMO-001", "ZT-2026-001"}

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
