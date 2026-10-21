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
    assert workspace["batch"]["story_json"]["ip_name"] == "乌蒙丑丑"
    assert workspace["runs"][0]["agent"] == "story"
    assert workspace["runs"][0]["status"] == "waiting_review"

    approved = await client.post(f"/api/batches/{batch_id}/agents/story/approve", json={})
    assert approved.status_code == 200
    assert approved.json()["batch"]["state"] == "story_approved"
    assert len(approved.json()["artifacts"]) == 1

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.json()["batch"]["state"] == "packaging_review"
    approved = await client.post(f"/api/batches/{batch_id}/agents/packaging/approve", json={})
    assert approved.json()["batch"]["state"] == "packaging_approved"

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.json()["batch"]["state"] == "marketing_review"
    approved = await client.post(f"/api/batches/{batch_id}/agents/marketing/approve", json={})
    assert approved.json()["batch"]["state"] == "marketing_approved"

    started = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert started.json()["batch"]["state"] == "pricing_review"
    approved = await client.post(f"/api/batches/{batch_id}/agents/pricing/approve", json={})
    assert approved.status_code == 200
    final = approved.json()
    assert final["batch"]["state"] == "traced"
    assert final["batch"]["trace_code"].startswith("ZT")
    assert final["batch"]["pricing_json"]["premium_pct"] == 156.0
    assert len(final["artifacts"]) == 4

    workspace = await client.get(f"/api/batches/{batch_id}/workspace")
    assert workspace.status_code == 200
    assert len(workspace.json()["artifacts"]) == 4
    assert {artifact["kind"] for artifact in workspace.json()["artifacts"]} == set(AGENTS)


async def test_pipeline_blocks_while_waiting_review(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)

    first = await client.post(f"/api/batches/{batch_id}/pipeline/start")
    assert first.status_code == 200
    second = await client.post(f"/api/batches/{batch_id}/pipeline/start")

    assert second.status_code == 409


async def test_pipeline_rejects_out_of_order_agent(session, client):
    batch_id = await _seed_and_get_raw_batch(client, session)

    response = await client.post(
        f"/api/batches/{batch_id}/agents/packaging/run", json={}
    )

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

    rerun = await client.post(f"/api/batches/{batch_id}/agents/story/run", json={"note": "再乡土一点"})
    assert rerun.status_code == 200
    assert rerun.json()["batch"]["state"] == "story_review"
    assert len(rerun.json()["runs"]) == 2
    assert rerun.json()["runs"][0]["status"] == "waiting_review"
