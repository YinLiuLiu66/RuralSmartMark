from sqlalchemy import select

from ruralsmartmark.agents.controller import ControllerTurn
from ruralsmartmark.models import Batch, ControllerSession, ProductProfile
from ruralsmartmark.schemas import (
    ResearchBenchmarkDraft,
    ResearchDocDraft,
    ResearchDraft,
    ResearchProduct,
)


def _draft() -> ResearchDraft:
    return ResearchDraft(
        product=ResearchProduct(
            slug="controller-fruit",
            name="总控测试水果",
            county="测试县",
            province="测试省",
            category="鲜果",
            form="1kg 礼盒",
        ),
        specs={"brand_name": "总控品牌", "ip_name": "总控守园人", "trace_prefix": "CT"},
        docs=[
            ResearchDocDraft(
                doc_id="ORIGIN-01",
                title="产地",
                type="产区",
                source_url="internal://test",
                source_date="2026-10-22",
                credibility="demo",
                content="总控测试产地说明，仅用于验证建档确认流程。",
            )
        ],
        benchmarks=[
            ResearchBenchmarkDraft(
                channel="散装批发",
                competitor="总控测试水果",
                spec="1kg",
                price_per_kg=10,
            ),
            ResearchBenchmarkDraft(
                channel="电商散装",
                competitor="总控测试水果",
                spec="1kg",
                price_per_kg=12,
            ),
            ResearchBenchmarkDraft(
                channel="品牌礼盒",
                competitor="总控测试水果",
                spec="1kg",
                price_per_kg=25,
            ),
        ],
    )


async def test_confirm_commit_product(session, client):
    draft = _draft()
    item = ControllerSession(
        draft_json=draft.model_dump(mode="json"),
        pending_action_json={
            "id": "act-1",
            "kind": "commit_product",
            "summary": "确认建立总控测试水果档案",
        },
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-1", "decision": "confirm"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["session"]["product_id"] is not None
    assert data["session"]["batch_id"] is not None
    assert data["session"]["draft_json"] is None
    assert data["session"]["pending_action_json"] is None

    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == "controller-fruit")
    )
    assert product is not None
    batch = await session.get(Batch, data["session"]["batch_id"])
    assert batch is not None
    assert batch.product_id == product.id


async def test_controller_message_persists_turn(session, client, monkeypatch):
    item = ControllerSession()
    session.add(item)
    await session.commit()
    await session.refresh(item)

    async def fake_turn(*_args, **_kwargs):
        return ControllerTurn(
            reply="我看到你了。",
            draft=None,
            pending=None,
            events=[],
            questions=[],
            thinking=["先确认用户只是打招呼。"],
        )

    monkeypatch.setattr("ruralsmartmark.routes.controller.run_controller_turn", fake_turn)
    response = await client.post(
        f"/api/controller/sessions/{item.id}/messages",
        json={"message": "你好"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["reply"] == "我看到你了。"
    assert data["thinking"] == ["先确认用户只是打招呼。"]
    assert [message["role"] for message in data["session"]["messages"]] == [
        "user",
        "assistant",
    ]


async def test_controller_message_streams_events(session, client, monkeypatch):
    item = ControllerSession()
    session.add(item)
    await session.commit()
    await session.refresh(item)

    async def fake_turn(*_args, emit=None, **_kwargs):
        assert emit is not None
        await emit({"type": "thinking", "text": "先想一下。\n再回答。"})
        await emit({"type": "delta", "text": "你好，"})
        await emit({"type": "delta", "text": "我在。"})
        return ControllerTurn(
            reply="你好，我在。",
            draft=None,
            pending=None,
            events=[],
            questions=[],
            thinking=["先想一下。", "再回答。"],
        )

    monkeypatch.setattr("ruralsmartmark.routes.controller.run_controller_turn", fake_turn)
    async with client.stream(
        "POST",
        f"/api/controller/sessions/{item.id}/messages/stream",
        json={"message": "在吗"},
    ) as response:
        assert response.status_code == 200, await response.aread()
        body = "".join([chunk async for chunk in response.aiter_text()])

    assert '"type": "user"' in body
    assert '"type": "thinking"' in body
    assert '"type": "delta"' in body
    assert '"type": "done"' in body
    assert "你好，我在。" in body

    refreshed = await client.get(f"/api/controller/sessions/{item.id}")
    messages = refreshed.json()["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["content"] == "你好，我在。"


async def test_fresh_session_reuses_single_blank_session(session, client):
    existing = ControllerSession()
    session.add(existing)
    await session.commit()
    await session.refresh(existing)

    response = await client.post(
        "/api/controller/sessions",
        json={"fresh": True},
    )
    assert response.status_code == 200, response.text
    reused = response.json()
    assert reused["id"] == existing.id
    assert reused["product_id"] is None
    assert reused["batch_id"] is None
    assert reused["messages"] == []

    again = await client.post("/api/controller/sessions", json={"fresh": True})
    assert again.status_code == 200
    assert again.json()["id"] == existing.id

    product = ProductProfile(
        slug="fresh-after-commit",
        name="建档后新产品",
        county="测试县",
        province="测试省",
        category="鲜果",
        form="1kg 礼盒",
    )
    session.add(product)
    await session.flush()
    existing.product_id = product.id
    await session.commit()

    after_commit = await client.post(
        "/api/controller/sessions",
        json={"fresh": True},
    )
    assert after_commit.status_code == 200
    assert after_commit.json()["id"] != existing.id


async def test_confirm_approve_continues_next_station(session, client, monkeypatch):
    product = ProductProfile(
        slug="auto-continue-fruit",
        name="自动继续水果",
        county="测试县",
        province="测试省",
        category="鲜果",
        form="1kg 礼盒",
    )
    session.add(product)
    await session.flush()
    batch = Batch(
        product_id=product.id,
        code="AC-001",
        state="story_review",
        current_station="story",
    )
    session.add(batch)
    await session.commit()
    await session.refresh(batch)

    item = ControllerSession(
        product_id=product.id,
        batch_id=batch.id,
        pending_action_json={
            "id": "act-approve",
            "kind": "approve_agent",
            "summary": "通过故事并自动运行包装设计",
            "agent": "story",
        },
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    calls: dict[str, str] = {}

    async def fake_approve(_session, target_batch, agent, _runtime):
        calls["approved"] = agent.value
        target_batch.state = "story_approved"

    async def fake_run(_session, target_batch, agent, _runtime, _note=None):
        calls["next"] = agent.value
        target_batch.state = "packaging_review"

        class _Run:
            status = "waiting_review"

        return _Run()

    monkeypatch.setattr("ruralsmartmark.routes.controller.approve_agent", fake_approve)
    monkeypatch.setattr(
        "ruralsmartmark.routes.controller.run_pipeline_agent", fake_run
    )

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-approve", "decision": "confirm"},
    )
    assert response.status_code == 200, response.text
    assert calls == {"approved": "story", "next": "packaging"}
    assert "已自动运行 packaging" in response.json()["reply"]
    assert "待审核" in response.json()["reply"]
