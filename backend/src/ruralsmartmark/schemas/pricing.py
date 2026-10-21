"""M6 溢价对照响应模型（decisions #31）。"""

from pydantic import BaseModel


class PriceBenchmarkOut(BaseModel):
    channel: str
    bulk_price: float
    brand_price: float
    premium_rate: float


class PricingOut(BaseModel):
    sku_id: int
    sku_name: str
    note: str
    items: list[PriceBenchmarkOut]
