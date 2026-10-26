import pytest
from sqlalchemy import select

from ruralsmartmark.models import Batch, ControllerSession, ProductProfile
from ruralsmartmark.services.batch_create import (
    DEFAULT_QUANTITY_KG,
    BatchCreateError,
    create_batch_for_product,
)


async def _make_product(session, *, slug: str = "create-fruit") -> ProductProfile:
    product = ProductProfile(
        slug=slug,
        name="建批测试水果",
        county="测试县",
        category="鲜果",
        form="1kg 礼盒",
        specs={"batch_prefix": "CJ"},
    )
    session.add(product)
    await session.flush()
    return product


async def test_create_batch_uses_prefix_and_increments(session):
    product = await _make_product(session)

    first = await create_batch_for_product(session, product)
    second = await create_batch_for_product(session, product, 500)

    assert first.code == "CJ-2026-001"
    assert second.code == "CJ-2026-002"
    assert first.state == "raw"
    assert first.current_station == "intake"
    assert first.quantity_kg == DEFAULT_QUANTITY_KG
    assert second.quantity_kg == 500


async def test_create_batch_rejects_nonpositive_quantity(session):
    product = await _make_product(session)

    with pytest.raises(BatchCreateError):
        await create_batch_for_product(session, product, 0)
    with pytest.raises(BatchCreateError):
        await create_batch_for_product(session, product, -5)


async def test_confirm_create_batch_flow(session, client):
    product = await _make_product(session)
    item = ControllerSession(
        product_id=product.id,
        pending_action_json={
            "id": "act-create",
            "kind": "create_batch",
            "summary": "为建批测试水果创建 500kg 新批次",
            "quantity_kg": 500,
        },
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    product_id = product.id

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-create", "decision": "confirm"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "创建新批次 CJ-2026-001" in data["reply"]
    assert data["session"]["batch_id"] is not None
    session.expire_all()  # API 在独立会话里写库，测试会话需失效缓存后重查
    batch = await session.get(Batch, data["session"]["batch_id"])
    assert batch is not None
    assert batch.product_id == product_id
    assert batch.code == "CJ-2026-001"
    assert batch.quantity_kg == 500


async def test_confirm_create_batch_without_product_refused(session, client):
    item = ControllerSession(
        pending_action_json={
            "id": "act-orphan",
            "kind": "create_batch",
            "summary": "没有产品也要开批次",
        },
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    response = await client.post(
        f"/api/controller/sessions/{item.id}/confirm",
        json={"action_id": "act-orphan", "decision": "confirm"},
    )

    assert response.status_code == 409
    assert "没有绑定产品" in response.json()["detail"]
    assert await session.scalar(select(Batch)) is None
