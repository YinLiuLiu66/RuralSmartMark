from datetime import datetime
from typing import Literal

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


class PackagingVariantOut(BaseModel):
    key: str
    name: str
    description: str
    swatches: list[str]


class TracePriceTier(BaseModel):
    channel: str
    pack: str
    price_per_kg: float
    price_total: float
    note: str


class TraceQA(BaseModel):
    q: str
    a: str


class TraceProductOut(BaseModel):
    name: str
    county: str
    province: str
    form: str
    brand_name: str
    ip_name: str
    specs: dict = Field(default_factory=dict)


class TraceBatchOut(BaseModel):
    code: str
    trace_code: str
    quantity_kg: float
    created_at: datetime


class TraceEvidenceOut(BaseModel):
    doc_id: str
    title: str
    source_url: str | None = None
    source_date: str | None = None
    credibility: str
    quote: str
    use: str | None = None


class TraceStoryOut(BaseModel):
    ip_name: str
    persona: str
    story_long: str
    story_short: str
    taglines: list[str]
    evidence: list[TraceEvidenceOut]
    illustration_url: str | None = None


class TracePackagingCopy(BaseModel):
    front: str
    back: str
    side: str
    inside: str


class TracePackagingOut(BaseModel):
    concept: str
    packaging_copy: TracePackagingCopy
    structure: dict[str, str]
    image_url: str


class TraceXiaohongshu(BaseModel):
    title: str
    body: str
    tags: list[str]
    cover_text: str


class TraceMarketingOut(BaseModel):
    xiaohongshu: TraceXiaohongshu
    douyin_hook: str
    wechat_title: str


class TracePricingOut(BaseModel):
    price_ladder: list[TracePriceTier]
    premium_pct: float
    rationale: str
    formula: str
    cost_breakdown: dict[str, float]
    faq: list[TraceQA]
    persona_greeting: str
    is_demo: bool


class TraceTimelineEvent(BaseModel):
    step: str
    note: str
    at: datetime | None = None


class TraceOut(BaseModel):
    trace_code: str
    batch: TraceBatchOut
    product: TraceProductOut
    story: TraceStoryOut
    packaging: TracePackagingOut
    marketing: TraceMarketingOut
    pricing: TracePricingOut
    timeline: list[TraceTimelineEvent]
    journey: list[TraceTimelineEvent]
    scan_count: int
    last_scanned_at: datetime | None = None
    demo: bool = True
    fixed_demo: bool = False


class TraceScanOut(BaseModel):
    scan_count: int
    recorded: bool = True


class TraceChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=300)


class TraceChatOut(BaseModel):
    reply: str
    source: Literal["llm", "template"]
