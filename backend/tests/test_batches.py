from ruralsmartmark.seed import PRODUCT_SLUG, seed_demo


async def test_create_and_get_batch(session, client):
    await seed_demo(session)

    response = await client.post(
        "/api/batches",
        json={"product_slug": PRODUCT_SLUG, "quantity_kg": 300},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["state"] == "raw"
    assert created["current_station"] == "intake"
    assert created["code"].startswith("ZT-")

    detail = await client.get(f"/api/batches/{created['id']}")
    assert detail.status_code == 200
    assert detail.json()["code"] == created["code"]


async def test_missing_batch_returns_404(client):
    response = await client.get("/api/batches/999999")

    assert response.status_code == 404
