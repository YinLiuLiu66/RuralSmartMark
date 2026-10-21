from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: str
    app: str
    db: str


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    county: str
    province: str
    category: str
    form: str
    specs: dict = Field(default_factory=dict)
    palette: dict = Field(default_factory=dict)
    scene_preset: str
    knowledge_dir: str
    is_active: bool


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    code: str
    quantity_kg: float
    state: str
    current_station: str
    trace_code: str | None = None
    created_at: datetime
    updated_at: datetime


class BatchCreate(BaseModel):
    product_slug: str = "zhaotong-ugly-apple"
    quantity_kg: float = Field(default=500.0, gt=0)


class DemoResetOut(BaseModel):
    products: int
    batches: int
