from ruralsmartmark.seed import seed_demo

AGENTS = ["story", "packaging", "marketing", "pricing"]


async def _traced_batch(client, session) -> str:
    await seed_demo(session)
    response = await client.get("/api/batches")
    assert response.status_code == 200
    raw = next(batch for batch in response.json() if batch["state"] == "raw")
    workspace = None
    for agent in AGENTS:
        started = await client.post(f"/api/batches/{raw['id']}/pipeline/start")
        assert started.status_code == 200
        approved = await client.post(
            f"/api/batches/{raw['id']}/agents/{agent}/approve",
            json={},
        )
        assert approved.status_code == 200
        workspace = approved.json()
    assert workspace is not None
    assert workspace["batch"]["state"] == "traced"
    return workspace["batch"]["trace_code"]


async def test_trace_public_payload(session, client):
    code = await _traced_batch(client, session)

    response = await client.get(f"/api/trace/{code.lower()}")
    assert response.status_code == 200
    data = response.json()
    assert data["trace_code"] == code
    assert data["story"]["ip_name"] == "山风守园人"
    assert data["product"]["brand_name"] == "乌蒙丑果"
    assert data["pricing"]["premium_pct"] == 156.0
    assert len(data["pricing"]["price_ladder"]) == 3
    assert "margin" not in data["pricing"]["price_ladder"][0]
    assert data["packaging"]["image_url"].endswith("/packaging.png")
    assert data["timeline"][0]["step"] == "批次建立"
    assert [item["step"] for item in data["timeline"][1:]] == [
        "故事定稿",
        "包装定稿",
        "内容定稿",
        "定价与溯源码",
    ]
    assert len(data["journey"]) >= 4
    assert len(data["story"]["evidence"]) >= 2
    assert data["fixed_demo"] is False


async def test_demo_reset_keeps_fixed_demo_trace(client):
    first = await client.post("/api/demo/reset")
    assert first.status_code == 200
    second = await client.post("/api/demo/reset")
    assert second.status_code == 200

    trace = await client.get("/api/trace/ZTDEMO26")
    assert trace.status_code == 200
    data = trace.json()
    assert data["fixed_demo"] is True
    assert data["story"]["ip_name"] == "山风守园人"
    assert data["pricing"]["premium_pct"] == 156.0
    assert [item["step"] for item in data["timeline"][1:]] == [
        "故事定稿",
        "包装定稿",
        "内容定稿",
        "定价与溯源码",
    ]
    assert (await client.get("/api/trace/ZTDEMO26/packaging.png")).status_code == 200
    assert (await client.get("/api/trace/ZTDEMO26/qr.png")).status_code == 200

    batches = (await client.get("/api/batches")).json()
    demo = next(batch for batch in batches if batch["code"] == "ZT-DEMO-001")
    workspace = (await client.get(f"/api/batches/{demo['id']}/workspace")).json()
    assert len(workspace["runs"]) == 4
    assert len(workspace["artifacts"]) == 4


async def test_trace_unknown_code_is_404(client):
    response = await client.get("/api/trace/NOPE-404")

    assert response.status_code == 404


async def test_trace_packaging_png(session, client):
    code = await _traced_batch(client, session)

    response = await client.get(f"/api/trace/{code}/packaging.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


async def test_trace_qr_and_scan_stats(session, client):
    code = await _traced_batch(client, session)

    qr = await client.get(f"/api/trace/{code}/qr.png")
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert qr.content.startswith(b"\x89PNG")

    stats = await client.get(f"/api/trace/{code}/scan")
    assert stats.status_code == 200
    assert stats.json() == {"scan_count": 0, "recorded": False}


async def test_scan_increments_and_is_visible(session, client):
    code = await _traced_batch(client, session)

    first = await client.post(f"/api/trace/{code}/scan")
    second = await client.post(f"/api/trace/{code}/scan")

    assert first.status_code == 200
    assert first.json()["scan_count"] == 1
    assert second.json()["scan_count"] == 2
    trace = await client.get(f"/api/trace/{code}")
    assert trace.json()["scan_count"] == 2
    assert trace.json()["last_scanned_at"] is not None


async def test_chat_uses_safe_template_without_provider(session, client):
    code = await _traced_batch(client, session)

    medical = await client.post(
        f"/api/trace/{code}/chat",
        json={"message": "这个苹果能降血糖吗？"},
    )
    assert medical.status_code == 200
    assert medical.json()["source"] == "template"
    assert "医疗" in medical.json()["reply"]

    price = await client.post(
        f"/api/trace/{code}/chat",
        json={"message": "为什么比散装贵？"},
    )
    assert price.status_code == 200
    assert price.json()["source"] == "template"
    assert "演示测算" in price.json()["reply"]

    empty = await client.post(f"/api/trace/{code}/chat", json={"message": ""})
    assert empty.status_code == 422
