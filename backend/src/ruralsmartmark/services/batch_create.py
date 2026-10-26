from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Batch, ProductProfile

DEFAULT_QUANTITY_KG = 300.0


class BatchCreateError(RuntimeError):
    """无法创建批次；消息可直接展示给用户。"""


async def next_batch_code(session: AsyncSession, product: ProductProfile) -> str:
    year = datetime.now().year
    raw_prefix = str((product.specs or {}).get("batch_prefix") or "ZT").strip() or "ZT"
    prefix = f"{raw_prefix[:6]}-{year}-"
    count = await session.scalar(
        select(func.count()).select_from(Batch).where(Batch.code.like(f"{prefix}%"))
    )
    return f"{prefix}{int(count or 0) + 1:03d}"


async def create_batch_for_product(
    session: AsyncSession,
    product: ProductProfile,
    quantity_kg: float = DEFAULT_QUANTITY_KG,
) -> Batch:
    """给产品创建下一编号批次；总控确认流与手动接口共用。"""
    if quantity_kg <= 0:
        raise BatchCreateError("批次数量必须大于 0 千克。")
    batch = Batch(
        product_id=product.id,
        code=await next_batch_code(session, product),
        quantity_kg=quantity_kg,
        state="raw",
        current_station="intake",
    )
    session.add(batch)
    await session.commit()
    await session.refresh(batch)
    return batch
