"""M2 sim 引擎验收：控制 / 快照 / WS 冒烟 + 一个完整周期的剧本双写推进。

TestClient 不进 lifespan → 引擎主循环在测试中不运转，与 asyncpg 事件循环互不干扰；
真实推进用 asyncio.run 显式驱动 script.step()（conftest 已把 db 换成测试库 NullPool）。
"""

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from ruralsmartmark import db
from ruralsmartmark.app import app
from ruralsmartmark.config import settings
from ruralsmartmark.models import Pallet, Shipment, TraceCode, TraceEvent
from ruralsmartmark.sim.engine import engine
from ruralsmartmark.sim.scenario import DEMO_TRACE_CODE

client = TestClient(app)

FORM = {"Content-Type": "application/x-www-form-urlencoded"}


def _token(username: str = "operator", password: str = "operator-demo") -> str:
    resp = client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
        headers=FORM,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _control(token: str, payload: dict) -> dict:
    resp = client.post(
        "/api/sim/control",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["clock"]


def test_control_speed_validation_422() -> None:
    token = _token()
    auth = {"Authorization": f"Bearer {token}"}
    for body in (
        {"action": "speed"},
        {"action": "speed", "speed": 0.5},
        {"action": "speed", "speed": 11},
        {"action": "reboot"},
    ):
        resp = client.post("/api/sim/control", json=body, headers=auth)
        assert resp.status_code == 422, body


def test_speed_then_pause_resume() -> None:
    token = _token()
    clock = _control(token, {"action": "speed", "speed": 5})
    assert clock["speed"] == 5.0
    clock = _control(token, {"action": "pause"})
    assert clock["running"] is False
    clock = _control(token, {"action": "resume"})
    assert clock["running"] is True


def test_reset_rebuilds_world_and_snapshot_public() -> None:
    token = _token()
    clock = _control(token, {"action": "reset"})
    assert clock["tick"] == 0
    assert clock["running"] is True
    assert clock["sim_time"].endswith("T07:00:00+08:00")

    # 快照公开读：沙盘首页加载先于登录（WS 同为不鉴权，decisions #19）
    resp = client.get("/api/world/snapshot")
    assert resp.status_code == 200
    world = resp.json()
    assert len(world["sites"]) == 4
    assert len(world["vehicles"]) == 2
    assert len(world["workers"]) == 5
    # 集货仓预置 4 托：世界一开演二程车就有货
    assert len(world["pallets"]) >= 4
    assert all(p["current_site_id"] is not None for p in world["pallets"])


def test_ws_world_receives_clock_events() -> None:
    token = _token()
    with client.websocket_connect("/ws/world") as ws:
        client.post(
            "/api/sim/control",
            json={"action": "pause"},
            headers={"Authorization": f"Bearer {token}"},
        )
        msg = ws.receive_json()
        assert msg["type"] == "tick.info"
        assert msg["data"]["running"] is False
        assert msg["sim_time"]


def test_scenario_one_cycle_dual_writes(monkeypatch) -> None:
    """真实驱动 101 个模拟分钟：运单五步走完、trace_event 按节点成行。"""
    # 固定 seed 保证告警数确定（种子值经实跑校验，见 05 M2 验收记录）
    monkeypatch.setattr(settings, "sim_seed", 7)

    async def main() -> None:
        await engine.reset()
        script = engine.script
        assert script is not None
        for _ in range(101):  # 覆盖第一个完整一程周期 + 下一周期起点
            async with db.session_factory() as session, session.begin():
                await script.step(session)
            engine.clock.advance()

        async with db.session_factory() as session:
            kinds = dict(
                (
                    await session.execute(
                        select(TraceEvent.kind, func.count())
                        .where(
                            ~TraceEvent.pallet_id.in_(
                                select(TraceCode.pallet_id).where(
                                    TraceCode.code == DEMO_TRACE_CODE
                                )
                            )
                        )
                        .group_by(TraceEvent.kind)
                    )
                ).all()
            )
            delivered = await session.scalar(
                select(func.count())
                .select_from(Shipment)
                .where(Shipment.status == "delivered")
            )
            hub_stock = await session.scalar(
                select(func.count())
                .select_from(Pallet)
                .where(Pallet.current_site_id == script.refs.site["hub"])
            )
            on_vehicle = await session.scalar(
                select(func.count())
                .select_from(Pallet)
                .where(Pallet.current_vehicle_id.is_not(None))
            )
        return kinds, delivered, hub_stock, on_vehicle

    kinds, delivered, hub_stock, on_vehicle = asyncio.run(main())

    # 双写核心证据：一程批次 4 托全链路节点 + 二程三层装/卸各 2 次（二程+三程）
    assert kinds["harvested"] == 8  # 两个周期起点（t=0 与 wrap 后的 t=0）
    assert kinds["packed"] == 4
    assert kinds["stored"] == 4
    assert kinds["loaded"] == 12  # 农场 4 + 集货仓 4 + 前置仓 4
    assert kinds["departed"] == 12
    assert kinds["arrived"] == 12
    assert kinds["unloaded"] == 12
    assert (delivered or 0) == 3  # 一程 + 二程 + 三程运单
    assert (hub_stock or 0) == 4  # 周期批次已入库，等待下一趟二程
    assert (on_vehicle or 0) == 0  # 101 分钟时点：卡车均已卸货/返场
    assert kinds.get("temp_alert", 0) >= 1  # 演示剧情：冷链越限告警至少一次


def test_final_leg_writes_delivered_trace(monkeypatch) -> None:
    """最终一程到门店才写 delivered；集货仓/前置仓到站不算签收。"""
    monkeypatch.setattr(settings, "sim_seed", 7)

    async def main() -> int:
        await engine.reset()
        script = engine.script
        assert script is not None
        for _ in range(175):
            async with db.session_factory() as session, session.begin():
                await script.step(session)
            engine.clock.advance()

        async with db.session_factory() as session:
            delivered = await session.scalar(
                select(func.count())
                .select_from(TraceEvent)
                .where(
                    TraceEvent.kind == "delivered",
                    ~TraceEvent.pallet_id.in_(
                        select(TraceCode.pallet_id).where(
                            TraceCode.code == DEMO_TRACE_CODE
                        )
                    ),
                )
            )
        return delivered or 0

    assert asyncio.run(main()) >= 1
