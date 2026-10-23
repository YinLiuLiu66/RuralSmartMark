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


class ResearchProduct(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)
    name: str = Field(min_length=1, max_length=120)
    county: str = Field(min_length=1, max_length=120)
    province: str = Field(default="", max_length=80)
    category: str = Field(min_length=1, max_length=80)
    form: str = Field(min_length=1, max_length=120)
    palette: dict[str, str] = Field(default_factory=dict)


class ResearchDocDraft(BaseModel):
    doc_id: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=40)
    source_url: str = Field(min_length=1, max_length=500)
    source_date: str = Field(min_length=1, max_length=20)
    credibility: str = Field(default="media", max_length=20)
    content: str = Field(min_length=10, max_length=3000)


class ResearchBenchmarkDraft(BaseModel):
    channel: Literal["散装批发", "电商散装", "品牌礼盒"]
    competitor: str = Field(min_length=1, max_length=120)
    spec: str = Field(min_length=1, max_length=120)
    price_per_kg: float = Field(gt=0, le=1000)
    source_url: str = Field(default="", max_length=500)
    source_date: str = Field(default="", max_length=20)
    note: str = Field(default="", max_length=255)


class ResearchSource(BaseModel):
    url: str = Field(min_length=4, max_length=500)
    title: str = Field(default="", max_length=200)


class ResearchDraft(BaseModel):
    product: ResearchProduct
    specs: dict = Field(default_factory=dict)
    docs: list[ResearchDocDraft] = Field(default_factory=list, max_length=30)
    benchmarks: list[ResearchBenchmarkDraft] = Field(default_factory=list, max_length=5)
    questions: list[str] = Field(default_factory=list, max_length=8)
    sources: list[ResearchSource] = Field(default_factory=list, max_length=30)
    warnings: list[str] = Field(default_factory=list, max_length=20)


class ControllerSessionCreate(BaseModel):
    product_slug: str | None = None
    batch_id: int | None = None
    fresh: bool = False


class ControllerMessageIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ControllerMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    action_json: dict | None = None
    created_at: datetime


class ControllerSessionOut(BaseModel):
    id: int
    product_id: int | None = None
    batch_id: int | None = None
    draft_json: dict | None = None
    pending_action_json: dict | None = None
    messages: list[ControllerMessageOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ControllerConfirmIn(BaseModel):
    action_id: str = Field(min_length=1, max_length=80)
    decision: Literal["confirm", "cancel"]


class ControllerTurnOut(BaseModel):
    session: ControllerSessionOut
    reply: str
    questions: list[str] = Field(default_factory=list)
    pending_action: dict | None = None
    events: list[dict] = Field(default_factory=list)
    thinking: list[str] = Field(default_factory=list)
