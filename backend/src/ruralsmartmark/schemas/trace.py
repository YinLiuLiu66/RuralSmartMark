"""溯源 H5 响应模型（M5，decisions #30）。"""

from pydantic import BaseModel


class TraceProductOut(BaseModel):
    sku_id: int
    name: str
    box_price: float
    batch_no: str
    qty: int


class TraceStoryOut(BaseModel):
    artifact_id: int
    content: str


class TraceEventOut(BaseModel):
    id: int
    kind: str
    label: str
    sim_time: str | None
    site_name: str | None
    vehicle_plate: str | None
    note: str | None
    temperature: float | None


class TraceOut(BaseModel):
    code: str
    is_demo: bool
    product: TraceProductOut
    story: TraceStoryOut | None
    timeline: list[TraceEventOut]
