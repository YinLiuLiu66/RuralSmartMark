"""公开溯源接口（M5，decisions #4/#30）。

时间线读 trace_event 流水；故事取最新 final 品牌故事原文。
码固定为 8 位 Base32 大写，查询时统一大写归一。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.db import get_session
from ruralsmartmark.models import (
    AgentArtifact,
    Pallet,
    ProductSku,
    Site,
    TraceCode,
    TraceEvent,
    Vehicle,
)
from ruralsmartmark.schemas.trace import (
    TraceEventOut,
    TraceOut,
    TraceProductOut,
    TraceStoryOut,
)
from ruralsmartmark.sim.scenario import DEMO_TRACE_CODE

router = APIRouter(tags=["trace"])

TRACE_LABELS = {
    "harvested": "采摘",
    "packed": "分拣包装",
    "stored": "预冷入库",
    "loaded": "装车",
    "departed": "发车",
    "arrived": "到站",
    "unloaded": "卸货",
    "delivered": "门店签收",
    "temp_alert": "温控告警",
}


@router.get("/api/trace/{code}", response_model=TraceOut)
async def get_trace(
    code: str,
    session: AsyncSession = Depends(get_session),  # noqa: B008 — FastAPI 依赖注入惯用法
) -> TraceOut:
    normalized = code.strip().upper()
    trace_code = await session.scalar(
        select(TraceCode).where(TraceCode.code == normalized)
    )
    if trace_code is None:
        raise HTTPException(status_code=404, detail="溯源码不存在")

    pallet = await session.get(Pallet, trace_code.pallet_id)
    if pallet is None:
        raise HTTPException(status_code=404, detail="溯源批次不存在")
    sku = await session.get(ProductSku, pallet.sku_id) if pallet.sku_id else None
    if sku is None:
        raise HTTPException(status_code=404, detail="产品信息缺失")

    events = (
        await session.scalars(
            select(TraceEvent)
            .where(TraceEvent.pallet_id == pallet.id)
            .order_by(TraceEvent.id)
        )
    ).all()

    site_ids = {e.site_id for e in events if e.site_id is not None}
    vehicle_ids = {e.vehicle_id for e in events if e.vehicle_id is not None}
    sites = (
        {
            s.id: s.name
            for s in (
                await session.scalars(select(Site).where(Site.id.in_(site_ids)))
            ).all()
        }
        if site_ids
        else {}
    )
    vehicles = (
        {
            v.id: v.plate
            for v in (
                await session.scalars(
                    select(Vehicle).where(Vehicle.id.in_(vehicle_ids))
                )
            ).all()
        }
        if vehicle_ids
        else {}
    )

    timeline = [
        TraceEventOut(
            id=e.id,
            kind=e.kind,
            label=TRACE_LABELS.get(e.kind, e.kind),
            sim_time=(e.payload or {}).get("sim_ts"),
            site_name=sites.get(e.site_id),
            vehicle_plate=vehicles.get(e.vehicle_id),
            note=e.note,
            temperature=(e.payload or {}).get("temperature"),
        )
        for e in sorted(
            events, key=lambda e: ((e.payload or {}).get("sim_ts") or "", e.id)
        )
    ]

    story = await session.scalar(
        select(AgentArtifact)
        .where(
            AgentArtifact.kind == "story",
            AgentArtifact.status == "final",
            AgentArtifact.content.is_not(None),
        )
        .order_by(AgentArtifact.id.desc())
        .limit(1)
    )

    return TraceOut(
        code=normalized,
        is_demo=normalized == DEMO_TRACE_CODE,
        product=TraceProductOut(
            sku_id=sku.id,
            name=sku.name,
            box_price=float(sku.box_price),
            batch_no=pallet.batch_no,
            qty=pallet.qty,
        ),
        story=TraceStoryOut(artifact_id=story.id, content=story.content)
        if story and story.content
        else None,
        timeline=timeline,
    )
