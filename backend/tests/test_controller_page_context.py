"""页面上下文解析（decisions #92）。"""

from sqlalchemy import select

from ruralsmartmark.agents.controller import ControllerTurn
from ruralsmartmark.models import Batch, ControllerMessage, ControllerSession, ProductProfile


def _product(slug: str, name: str) -> ProductProfile:
    return ProductProfile(
        slug=slug,
        name=name,
        county="测试县",
        province="测试省",
        category="鲜果",
        form="1kg 礼盒",
    )


async def _prepare(session):
    first = _product("page-ctx-first", "第一产品")
    second = _product("page-ctx-second", "第二产品")
    session.add_all([first, second])
    await session.flush()
    batch = Batch(product_id=first.id, code="PC-001", state="raw", current_station="intake")
    session.add(batch)
    item = ControllerSession()
    session.add(item)
    await session.commit()
    await session.refresh(batch)
    await session.refresh(item)
    return first, second, batch, item


def _patch_turn(monkeypatch, captured: dict):
    async def fake(
        session,
        runtime,
        controller_session,
        message,
        *,
        search,
        page=None,
        history=None,
        emit=None,
    ):
        captured["page"] = page
        captured["history"] = history
        return ControllerTurn(reply="收到", draft=None, pending=None, events=[])

    monkeypatch.setattr("ruralsmartmark.routes.controller.run_controller_turn", fake)


async def test_page_context_resolves_and_labels_history(session, client, monkeypatch):
    first, _second, batch, item = await _prepare(session)
    captured: dict = {}
    _patch_turn(monkeypatch, captured)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/messages",
        json={
            "message": "现在到哪了？",
            "context": {
                "route": "project",
                "product_slug": first.slug,
                "batch_id": batch.id,
                "focus_agent": "packaging",
            },
        },
    )
    assert response.status_code == 200, response.text
    page = captured["page"]
    assert page.product is not None and page.product.slug == first.slug
    assert page.batch is not None and page.batch.code == "PC-001"
    assert page.focus_agent == "packaging"

    rows = (
        await session.execute(
            select(ControllerMessage).where(ControllerMessage.session_id == item.id)
        )
    ).scalars()
    user_row = next(row for row in rows if row.role == "user")
    assert user_row.action_json["page_label"] == "第一产品 / PC-001"

    refreshed = await client.get(f"/api/controller/sessions/{item.id}")
    assert refreshed.status_code == 200
    assert refreshed.json()["messages"][0]["action_json"]["page_context"]["batch"]["code"] == "PC-001"


async def test_page_context_rejects_foreign_batch(session, client):
    _first, second, batch, item = await _prepare(session)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/messages",
        json={
            "message": "通过包装",
            "context": {"route": "project", "product_slug": second.slug, "batch_id": batch.id},
        },
    )
    assert response.status_code == 400
    assert "不属于该产品" in response.json()["detail"]


async def test_page_context_rejects_missing_batch(session, client):
    first, _second, batch, item = await _prepare(session)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/messages",
        json={
            "message": "通过包装",
            "context": {"route": "project", "product_slug": first.slug, "batch_id": batch.id + 999},
        },
    )
    assert response.status_code == 400
    assert "批次不存在" in response.json()["detail"]


async def test_missing_page_context_still_answers(session, client, monkeypatch):
    _first, _second, _batch, item = await _prepare(session)
    captured: dict = {}
    _patch_turn(monkeypatch, captured)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/messages",
        json={"message": "我有哪些项目？"},
    )
    assert response.status_code == 200, response.text
    page = captured["page"]
    assert page.product is None
    assert page.batch is None

    rows = (
        (
            await session.execute(
                select(ControllerMessage).where(ControllerMessage.session_id == item.id)
            )
        )
        .scalars()
        .all()
    )
    user_row = next(row for row in rows if row.role == "user")
    assert user_row.action_json is None
