"""公开溢价对照接口（M6，decisions #31）。

数据为三档演示测算：散装行情为演示值，礼盒价取 SKU 定价；
溢价率 = (brand_price - bulk_price) / bulk_price。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ruralsmartmark.db import get_session
from ruralsmartmark.models import PriceBenchmark, ProductSku
from ruralsmartmark.schemas.pricing import PriceBenchmarkOut, PricingOut

router = APIRouter(tags=["pricing"])

PRICING_NOTE = (
    "演示测算：散装行情为演示值，礼盒价取产品定价；"
    "溢价率 =（礼盒价 - 散装价）/ 散装价。"
)


@router.get("/api/pricing/benchmarks", response_model=PricingOut)
async def pricing_benchmarks(
    session: AsyncSession = Depends(get_session),  # noqa: B008 — FastAPI 依赖注入惯用法
) -> PricingOut:
    sku = await session.scalar(
        select(ProductSku).where(ProductSku.name == "麻江蓝莓文创礼盒")
    )
    if sku is None:
        raise HTTPException(status_code=404, detail="产品不存在")

    rows = (
        await session.scalars(
            select(PriceBenchmark)
            .where(PriceBenchmark.sku_id == sku.id)
            .order_by(PriceBenchmark.id)
        )
    ).all()

    return PricingOut(
        sku_id=sku.id,
        sku_name=sku.name,
        note=PRICING_NOTE,
        items=[
            PriceBenchmarkOut(
                channel=row.channel,
                bulk_price=float(row.bulk_price),
                brand_price=float(row.brand_price),
                premium_rate=float(row.premium_rate),
            )
            for row in rows
        ],
    )
