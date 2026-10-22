from sqlalchemy import select

from ruralsmartmark.agents.base import AgentName
from ruralsmartmark.agents.runtime import get_runtime
from ruralsmartmark.main import app
from ruralsmartmark.models import Artifact, Batch
from ruralsmartmark.seed import seed_demo
from ruralsmartmark.services.rewind import rewind_to_agent

AGENTS = ["story", "packaging", "marketing", "pricing"]


async def _trace_raw_batch(client) -> int:
    batches = (await client.get("/api/batches")).json()
    raw = next(item for item in batches if item["state"] == "raw")
    for agent in AGENTS:
        started = await client.post(f"/api/batches/{raw['id']}/pipeline/start")
        assert started.status_code == 200, started.text
        approved = await client.post(
            f"/api/batches/{raw['id']}/agents/{agent}/approve", json={}
        )
        assert approved.status_code == 200, approved.text
    return raw["id"]


async def test_rewind_invalidates_downstream(session, client):
    await seed_demo(session)
    batch_id = await _trace_raw_batch(client)

    batch = await session.get(Batch, batch_id)
    assert batch is not None
    assert batch.state == "traced"
    assert batch.trace_code

    runtime = app.dependency_overrides[get_runtime]()
    run = await rewind_to_agent(
        session,
        batch,
        AgentName.PACKAGING,
        runtime,
        "包装改克制一点",
    )
    await session.refresh(batch)

    assert run.agent == "packaging"
    assert run.note == "包装改克制一点"
    assert batch.state == "packaging_review"
    assert batch.story_json is not None
    assert batch.packaging_json is not None
    assert batch.marketing_json is None
    assert batch.pricing_json is None
    assert batch.trace_code is None

    artifacts = list(
        (
            await session.execute(
                select(Artifact).where(Artifact.batch_id == batch_id)
            )
        )
        .scalars()
        .all()
    )
    assert {artifact.kind for artifact in artifacts} == {"story"}
