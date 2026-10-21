"""从数据库提取 3–6 条运营事实，注入 Agent Prompt（decisions #27）。

只取少量可核对的数字，不把世界快照整段塞进上下文；表为空时返回空列表，
Prompt 仍可依靠固定素材包工作（测试环境常见）。
"""

from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.models import (
    Cooperative,
    Pallet,
    ProductSku,
    Shipment,
    Site,
    Telemetry,
)


async def collect_facts(session: AsyncSession, sku_id: int | None = None) -> list[str]:
    facts: list[str] = []

    if sku_id is not None:
        sku = await session.get(ProductSku, sku_id)
        if sku is not None:
            facts.append(
                f"产品：{sku.name}，礼盒定价 {float(sku.box_price):.0f} 元。"
            )

    coop = await session.scalar(select(Cooperative).order_by(Cooperative.id).limit(1))
    if coop is not None:
        facts.append(
            f"主体：{coop.name}，产地 {coop.region or '麻江县'}（合作社名为演示虚构）。"
        )

    sites = (await session.scalars(select(Site).order_by(Site.id))).all()
    if sites:
        facts.append("链路节点：" + " → ".join(s.name for s in sites) + "。")

    temp_min, temp_max = (
        await session.execute(
            select(func.min(Telemetry.temperature), func.max(Telemetry.temperature))
        )
    ).one()
    if temp_min is not None and temp_max is not None:
        facts.append(
            f"冷链车厢实测温度 {float(temp_min):.1f}–{float(temp_max):.1f}℃。"
        )

    shipments = (
        await session.scalars(
            select(Shipment).where(
                Shipment.departed_at.is_not(None),
                Shipment.delivered_at.is_not(None),
            )
        )
    ).all()
    durations = [
        (s.delivered_at - s.departed_at).total_seconds() / 60
        for s in shipments
        if s.delivered_at is not None and s.departed_at is not None
    ]
    if durations:
        avg_minutes = round(mean(durations))
        facts.append(
            f"已送达运单 {len(durations)} 单，平均干线运输约 {avg_minutes} 分钟。"
        )

    pallet_count = await session.scalar(select(func.count()).select_from(Pallet))
    if pallet_count:
        facts.append(f"当前在库托盘 {pallet_count} 托。")

    return facts[:6]
