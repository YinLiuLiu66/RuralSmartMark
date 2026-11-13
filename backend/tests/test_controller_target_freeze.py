"""确认卡目标冻结（decisions #92）：目标只认 pending，且状态/草案变化即拒绝。"""

from ruralsmartmark.models import Batch, ControllerSession, ProductProfile
from ruralsmartmark.schemas import ResearchDraft, ResearchProduct


def _product(slug: str, name: str) -> ProductProfile:
    return ProductProfile(
        slug=slug,
        name=name,
        county="测试县",
        province="测试省",
        category="鲜果",
        form="1kg 礼盒",
    )


def _draft(slug: str) -> dict:
    draft = ResearchDraft(
        product=ResearchProduct(
            slug=slug,
            name="草案产品",
            county="测试县",
            province="测试省",
            category="鲜果",
            form="1kg 礼盒",
        ),
        specs={"brand_name": "草案品牌"},
    )
    return draft.model_dump(mode="json")


async def _session_with_pending(session, pending: dict, **fields) -> ControllerSession:
    item = ControllerSession(pending_action_json=pending, **fields)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def test_confirm_rejects_changed_batch_state(session, client):
    product = _product("freeze-state", "冻结状态水果")
    session.add(product)
    await session.flush()
    batch = Batch(
        product_id=product.id, code="FZ-001", state="story_review", current_station="story"
    )
    session.add(batch)
    await session.commit()
    await session.refresh(batch)

    item = await _session_with_pending(
        session,
        {
            "id": "act-state",
            "kind": "approve_agent",
            "summary": "通过故事",
            "agent": "story",
            "batch_id": batch.id,
            "batch_state": "story_review",
        },
    )

    # 出卡之后批次被别处改动。
    batch.state = "story_approved"
    await session.commit()

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-state", "decision": "confirm"},
    )
    assert response.status_code == 409
    assert "批次状态已变化" in response.json()["detail"]


async def test_confirm_rejects_missing_target(session, client):
    item = await _session_with_pending(
        session,
        {
            "id": "act-no-target",
            "kind": "approve_agent",
            "summary": "通过故事",
            "agent": "story",
        },
    )

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-no-target", "decision": "confirm"},
    )
    assert response.status_code == 409
    assert "缺少批次目标" in response.json()["detail"]


async def test_confirm_rejects_draft_hash_drift(session, client):
    item = await _session_with_pending(
        session,
        {
            "id": "act-draft",
            "kind": "commit_product",
            "summary": "确认建档",
            "draft_sha256": "stale-hash",
        },
        draft_json=_draft("freeze-draft"),
    )

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-draft", "decision": "confirm"},
    )
    assert response.status_code == 409
    assert "草案已被新的调研或录入覆盖" in response.json()["detail"]


async def test_apply_inputs_rejects_foreign_draft(session, client):
    product = _product("freeze-target", "目标水果")
    session.add(product)
    await session.commit()
    await session.refresh(product)

    item = await _session_with_pending(
        session,
        {
            "id": "act-foreign",
            "kind": "apply_inputs",
            "summary": "写入成本口径",
            "product_id": product.id,
        },
        product_id=product.id,
        draft_json=_draft("some-other-product"),
    )

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-foreign", "decision": "confirm"},
    )
    assert response.status_code == 409
    assert "与确认卡目标" in response.json()["detail"]
