from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from ruralsmartmark.models import (
    AgentRun,
    Artifact,
    Batch,
    ChatMessage,
    ControllerSession,
    ProductProfile,
    ScanEvent,
)
from ruralsmartmark.services.batch_delete import (
    BatchDeleteError,
    delete_batch,
    ensure_deletable,
)


async def _make_batch(session, *, code: str = "ZT-2026-901") -> tuple[ProductProfile, Batch]:
    product = ProductProfile(
        slug="delete-fruit",
        name="删除测试水果",
        county="测试县",
        category="鲜果",
        form="1kg 礼盒",
    )
    session.add(product)
    await session.flush()
    batch = Batch(product_id=product.id, code=code)
    session.add(batch)
    await session.flush()
    return product, batch


async def test_delete_batch_cascades_rows_and_files(session, tmp_path):
    _product, batch = await _make_batch(session)
    artifact_file = tmp_path / "artifacts" / "packaging.png"
    artifact_file.parent.mkdir(parents=True, exist_ok=True)
    artifact_file.write_bytes(b"png")
    run = AgentRun(batch_id=batch.id, agent="story", status="approved")
    artifact = Artifact(
        batch_id=batch.id,
        agent_run_id=None,
        kind="packaging",
        file_path=str(artifact_file),
    )
    scan = ScanEvent(batch_id=batch.id, trace_code="ZT9999")
    chat = ChatMessage(batch_id=batch.id, role="assistant", content="演示回答")
    session.add_all([run, artifact, scan, chat])
    await session.commit()
    batch_id = batch.id

    stats = await delete_batch(session, batch)

    assert stats == {"code": "ZT-2026-901", "runs": 1, "artifacts": 1, "files": 1}
    assert not artifact_file.exists()
    assert await session.get(Batch, batch_id) is None
    assert await session.scalar(select(AgentRun).where(AgentRun.batch_id == batch_id)) is None
    assert (
        await session.scalar(select(Artifact).where(Artifact.batch_id == batch_id)) is None
    )
    assert (
        await session.scalar(select(ScanEvent).where(ScanEvent.batch_id == batch_id)) is None
    )
    assert (
        await session.scalar(select(ChatMessage).where(ChatMessage.batch_id == batch_id))
        is None
    )


async def test_delete_batch_refuses_demo_batch(session):
    _product, batch = await _make_batch(session, code="ZT-DEMO-001")

    try:
        await ensure_deletable(session, batch)
    except BatchDeleteError as exc:
        assert "固定演示批次" in str(exc)
    else:
        raise AssertionError("演示批次应拒绝删除")


async def test_delete_batch_refuses_fresh_running_run(session):
    _product, batch = await _make_batch(session)
    session.add(AgentRun(batch_id=batch.id, agent="story", status="running"))
    await session.commit()

    try:
        await ensure_deletable(session, batch)
    except BatchDeleteError as exc:
        assert "正在运行" in str(exc)
    else:
        raise AssertionError("运行中的批次应拒绝删除")


async def test_delete_batch_allows_stale_running_run(session):
    _product, batch = await _make_batch(session)
    stale = AgentRun(batch_id=batch.id, agent="story", status="running")
    session.add(stale)
    await session.commit()
    stale.started_at = datetime.now(UTC) - timedelta(seconds=601)
    await session.commit()

    stats = await delete_batch(session, batch)

    assert stats["runs"] == 1
    assert await session.get(Batch, batch.id) is None


async def test_confirm_delete_batch_flow(session, client):
    _product, batch = await _make_batch(session)
    item = ControllerSession(
        product_id=_product.id,
        batch_id=batch.id,
        pending_action_json={
            "id": "act-del",
            "kind": "delete_batch",
            "summary": "确认删除批次 ZT-2026-901，删除不可恢复",
        },
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    batch_id = batch.id

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-del", "decision": "confirm"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "已删除批次 ZT-2026-901" in data["reply"]
    assert data["session"]["batch_id"] is None
    assert data["session"]["pending_action_json"] is None
    session.expire_all()  # API 在独立会话里删除，测试会话需失效缓存后重查
    assert await session.get(Batch, batch_id) is None


async def test_confirm_delete_batch_demo_refused(session, client):
    _product, batch = await _make_batch(session, code="ZT-DEMO-001")
    item = ControllerSession(
        product_id=_product.id,
        batch_id=batch.id,
        pending_action_json={
            "id": "act-demo",
            "kind": "delete_batch",
            "summary": "确认删除固定演示批次",
        },
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-demo", "decision": "confirm"},
    )

    assert response.status_code == 409
    assert "固定演示批次" in response.json()["detail"]
    assert await session.get(Batch, batch.id) is not None
