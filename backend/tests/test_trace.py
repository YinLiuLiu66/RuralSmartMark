"""M5 溯源接口验收：公开读、固定演示码、完整时间线与最终故事。"""

import asyncio

from fastapi.testclient import TestClient

from ruralsmartmark import db
from ruralsmartmark.app import app
from ruralsmartmark.models import AgentArtifact, AgentTask
from ruralsmartmark.sim.engine import engine
from ruralsmartmark.sim.scenario import DEMO_TRACE_CODE

client = TestClient(app)


async def _prepare() -> None:
    await engine.reset()
    async with db.session_factory() as session:
        task = AgentTask(agent_type="story", created_by="operator", status="done")
        session.add(task)
        await session.flush()
        session.add(
            AgentArtifact(
                task_id=task.id,
                kind="story",
                content="测试品牌故事（M5）",
                status="final",
            )
        )
        await session.commit()


def test_trace_demo_public_and_complete() -> None:
    asyncio.run(_prepare())
    resp = client.get(f"/api/trace/{DEMO_TRACE_CODE}")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["code"] == DEMO_TRACE_CODE
    assert data["is_demo"] is True
    assert data["product"]["name"] == "麻江蓝莓文创礼盒"
    assert data["product"]["batch_no"] == "MJ-DEMO-001"
    assert data["product"]["qty"] == 96
    assert data["story"]["content"] == "测试品牌故事（M5）"

    timeline = data["timeline"]
    assert len(timeline) == 17
    assert timeline[0]["kind"] == "harvested"
    assert timeline[0]["site_name"] == "龙山镇蓝莓基地 · 产地"
    assert timeline[-1]["kind"] == "delivered"
    assert timeline[-1]["site_name"] == "凯里门店 · 礼盒专区"
    assert any(
        e["kind"] == "temp_alert" and e["temperature"] == 8.4 for e in timeline
    )
    assert all(e["label"] for e in timeline)


def test_trace_lowercase_and_unknown() -> None:
    asyncio.run(_prepare())
    resp = client.get(f"/api/trace/{DEMO_TRACE_CODE.lower()}")
    assert resp.status_code == 200
    assert resp.json()["code"] == DEMO_TRACE_CODE

    missing = client.get("/api/trace/NOTACODE")
    assert missing.status_code == 404
