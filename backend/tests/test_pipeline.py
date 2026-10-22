import json

from ruralsmartmark.seed import seed_demo

AGENTS = ["story", "packaging", "marketing", "pricing"]


async def _seed_and_get_raw_batch(client, session) -> int:
    await seed_demo(session)
    response = await client.get("/api/batches")
    assert response.status_code == 200
    raw = next(batch for batch in response.json() if batch["state"] == "raw")
    return raw["id"]


async def test_pipeline_end_to_end(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.status_code == 200
    workspace = started.json()
    assert workspace["batch"]["state"] == "story_review"
    assert workspace["batch"]["story_json"]["ip_name"] == "山风守园人"
    assert workspace["runs"][0]["agent"] == "story"
    assert workspace["runs"][0]["status"] == "waiting_review"
    assert workspace["runs"][0]["model"] == "mock"
    assert workspace["runs"][0]["tokens"] == 0
    assert workspace["runs"][0]["guard_json"]["passed"] is True
    assert len(workspace["batch"]["story_json"]["cultural_evidence"]) >= 2

    approved = await client.post(f"/api/batches/{batch_id}/agents/story/approve", json={})
    assert approved.status_code == 200
    assert approved.json()["batch"]["state"] == "story_approved"
    assert len(approved.json()["artifacts"]) == 1

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.json()["batch"]["state"] == "packaging_review"

    preview = await client.get(f"/api/batches/{batch_id}/agents/packaging/preview")
    assert preview.status_code == 200
    assert preview.headers["content-type"] == "image/png"
    assert preview.content.startswith(b"\x89PNG")

    approved = await client.post(f"/api/batches/{batch_id}/agents/packaging/approve", json={})
    assert approved.json()["batch"]["state"] == "packaging_approved"
    packaging_artifact = next(
        item for item in approved.json()["artifacts"] if item["kind"] == "packaging"
    )
    assert packaging_artifact["file_url"] == f"/api/artifacts/{packaging_artifact['id']}/file"
    image = await client.get(packaging_artifact["file_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content.startswith(b"\x89PNG")

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.json()["batch"]["state"] == "marketing_review"
    approved = await client.post(f"/api/batches/{batch_id}/agents/marketing/approve", json={})
    assert approved.json()["batch"]["state"] == "marketing_approved"

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.json()["batch"]["state"] == "pricing_review"
    tampered = json.loads(json.dumps(started.json()["batch"]["pricing_json"]))
    tampered["premium_pct"] = 999
    tampered["price_ladder"][2]["price_total"] = 999
    approved = await client.post(
        f"/api/batches/{batch_id}/agents/pricing/approve",
        json={"output": tampered},
    )
    assert approved.status_code == 200
    final = approved.json()
    assert final["batch"]["state"] == "traced"
    assert final["batch"]["trace_code"].startswith("ZT")
    pricing = final["batch"]["pricing_json"]
    assert pricing["premium_pct"] == 156.0
    assert pricing["price_ladder"][2]["price_total"] == 128.0
    assert "156.0%" in pricing["formula"]
    assert pricing["is_demo"] is True
    assert pricing["qr_payload"].endswith(f"/trace/{final['batch']['trace_code']}")
    assert len(final["artifacts"]) == 4

    workspace = await client.get(f"/api/batches/{batch_id}/workspace")
    assert workspace.status_code == 200
    assert len(workspace.json()["artifacts"]) == 4
    assert {artifact["kind"] for artifact in workspace.json()["artifacts"]} == set(AGENTS)


async def test_approval_rejects_unsafe_edit(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)
    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    output = started.json()["batch"]["story_json"]

    unsafe = {**output, "story_long": output["story_long"] + "这是有机认证苹果，能降血糖。"}
    rejected = await client.post(
        f"/api/batches/{batch_id}/agents/story/approve",
        json={"output": unsafe},
    )
    assert rejected.status_code == 422
    assert "事实校验未通过" in rejected.json()["detail"]

    current = await client.get(f"/api/batches/{batch_id}/workspace")
    assert current.json()["batch"]["state"] == "story_review"

    approved = await client.post(f"/api/batches/{batch_id}/agents/story/approve", json={})
    assert approved.status_code == 200
    assert approved.json()["batch"]["state"] == "story_approved"


async def test_pipeline_blocks_while_waiting_review(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)

    first = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert first.status_code == 200
    second = await client.post(f"/api/batches/{batch_id}/pipeline/start")

    assert second.status_code == 409


async def test_pipeline_rejects_out_of_order_agent(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)

    response = await client.post(f"/api/batches/{batch_id}/agents/packaging/run", json={})

    assert response.status_code == 409


async def test_pipeline_reject_and_rerun(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)
    await client.post(f"/api/batches/{batch_id}/pipeline/start")

    rejected = await client.post(
        f"/api/batches/{batch_id}/agents/story/reject",
        json={"note": "再乡土一点"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["batch"]["state"] == "story_review"
    assert rejected.json()["runs"][0]["status"] == "failed"

    rerun = await client.post(
        f"/api/batches/{batch_id}/agents/story/run", json={"note": "再乡土一点"}
    )
    assert rerun.status_code == 200
    assert rerun.json()["batch"]["state"] == "story_review"
    assert len(rerun.json()["runs"]) == 2
    assert rerun.json()["runs"][0]["status"] == "waiting_review"
