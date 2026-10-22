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


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    agent: str
    status: str
    note: str | None = None
    output_json: dict | None = None
    guard_json: dict | None = None
    error: str | None = None
    model: str | None = None
    tokens: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    kind: str
    content_json: dict | None = None
    file_path: str | None = None
    file_url: str | None = None
    approved_at: datetime | None = None


class BatchFullOut(BatchOut):
    story_json: dict | None = None
    packaging_json: dict | None = None
    marketing_json: dict | None = None
    pricing_json: dict | None = None


class BatchWorkspaceOut(BaseModel):
    batch: BatchFullOut
    runs: list[AgentRunOut]
    artifacts: list[ArtifactOut]


class AgentRunRequest(BaseModel):
    note: str | None = None


class ApproveRequest(BaseModel):
    output: dict | None = None


class RejectRequest(BaseModel):
    note: str | None = None


class KnowledgeDocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_key: str
    title: str
    type: str
    source_url: str | None = None
    source_date: str | None = None
    credibility: str
