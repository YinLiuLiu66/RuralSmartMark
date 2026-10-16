"""沙盘快照 + WS 增量流（decisions #17：REST 快照为主，WS 只发增量）。

快照读现势实体表 + 引擎内存路线；WS 与快照同流同数据（#19：不区分角色、不鉴权）——
快照若设权限、WS 却裸奔，等于没有权限，索性两者都公开读。
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.db import get_session
from ruralsmartmark.models import Pallet, Shipment, Site, Vehicle, Worker
from ruralsmartmark.sim.engine import engine
from ruralsmartmark.ws.bus import bus

router = APIRouter(tags=["world"])


@router.get("/api/world/snapshot")
async def world_snapshot(
    session: AsyncSession = Depends(get_session),  # noqa: B008 — FastAPI 依赖注入惯用法
) -> dict[str, object]:
    sites = (await session.execute(select(Site).order_by(Site.id))).scalars().all()
    vehicles = (
        (await session.execute(select(Vehicle).order_by(Vehicle.id))).scalars().all()
    )
    workers = (
        (await session.execute(select(Worker).order_by(Worker.id))).scalars().all()
    )
    pallets = (
        (await session.execute(select(Pallet).order_by(Pallet.id))).scalars().all()
    )

    active = (
        (
            await session.execute(
                select(Shipment)
                .where(Shipment.status != "delivered")
                .order_by(Shipment.id)
            )
        )
        .scalars()
        .all()
    )
    recent_delivered = (
        (
            await session.execute(
                select(Shipment)
                .where(Shipment.status == "delivered")
                .order_by(Shipment.id.desc())
                .limit(10)
            )
        )
        .scalars()
        .all()
    )
    shipments = sorted({*active, *recent_delivered}, key=lambda s: s.id)

    routes = engine.routes_snapshot()
    empty_route: dict[str, object] = {}
    return {
        "clock": engine.clock_snapshot(),
        "sites": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "status": s.status,
                "capacity": s.capacity,
                "pos_x": float(s.pos_x),
                "pos_z": float(s.pos_z),
            }
            for s in sites
        ],
        "vehicles": [
            {
                "id": v.id,
                "plate": v.plate,
                "status": v.status,
                "temperature": float(v.temperature)
                if v.temperature is not None
                else None,
                "humidity": float(v.humidity) if v.humidity is not None else None,
                "current_site_id": v.current_site_id,
                "route": routes.get(v.id, empty_route) or None,
            }
            for v in vehicles
        ],
        "workers": [
            {
                "id": w.id,
                "site_id": w.site_id,
                "name": w.name,
                "status": w.status,
                "moves_today": w.moves_today,
            }
            for w in workers
        ],
        "pallets": [
            {
                "id": p.id,
                "sku_id": p.sku_id,
                "qty": p.qty,
                "batch_no": p.batch_no,
                "current_site_id": p.current_site_id,
                "current_vehicle_id": p.current_vehicle_id,
            }
            for p in pallets
        ],
        "shipments": [
            {
                "id": s.id,
                "from_site_id": s.from_site_id,
                "to_site_id": s.to_site_id,
                "vehicle_id": s.vehicle_id,
                "status": s.status,
                "departed_at": s.departed_at.isoformat(timespec="seconds")
                if s.departed_at
                else None,
                "delivered_at": s.delivered_at.isoformat(timespec="seconds")
                if s.delivered_at
                else None,
            }
            for s in shipments
        ],
    }


@router.websocket("/ws/world")
async def ws_world(ws: WebSocket) -> None:
    """增量事件流；连接后收到的客户端文本只当心跳，不承载指令。"""
    await bus.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        bus.disconnect(ws)
