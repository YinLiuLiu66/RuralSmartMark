from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .base import AgentName

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=2, max_length=20)
    quote: str = Field(min_length=8, max_length=180)
    use: str = Field(min_length=2, max_length=60)


class StoryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ip_name: str = Field(min_length=2, max_length=20)
    persona: str = Field(min_length=10, max_length=240)
    story_long: str = Field(min_length=200, max_length=1400)
    story_short: str = Field(min_length=8, max_length=60)
    taglines: list[str] = Field(min_length=2, max_length=5)
    cultural_evidence: list[Citation] = Field(min_length=1, max_length=4)
    tone_guide: str = Field(min_length=10, max_length=300)
    demo: bool = False
    fallback_reason: str | None = None

    @field_validator("taglines")
    @classmethod
    def _taglines_not_blank(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("taglines 不能有空字符串")
        return value


class PackagingCopy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    front: str = Field(min_length=2, max_length=30)
    back: str = Field(min_length=5, max_length=160)
    side: str = Field(min_length=2, max_length=40)
    inside: str = Field(min_length=2, max_length=80)


class PackagingStructure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    box_type: str = Field(min_length=2, max_length=60)
    dimensions: str = Field(min_length=4, max_length=60)
    material: str = Field(min_length=2, max_length=100)


class PackagingCost(BaseModel):
    model_config = ConfigDict(extra="forbid")

    box: float = Field(ge=0, le=100)
    tray: float = Field(ge=0, le=100)
    print: float = Field(ge=0, le=100)
    total: float = Field(ge=0, le=300)
    currency: str = "CNY"

    @model_validator(mode="after")
    def _total_matches(self) -> PackagingCost:
        expected = round(self.box + self.tray + self.print, 2)
        if abs(expected - self.total) > 0.01:
            raise ValueError(f"cost_estimate.total 应等于 {expected}")
        return self


class PackagingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept: str = Field(min_length=4, max_length=80)
    palette: list[str] = Field(min_length=3, max_length=5)
    typography: str = Field(min_length=4, max_length=120)
    ip_image_prompt: str = Field(min_length=10, max_length=300)
    packaging_copy: PackagingCopy
    structure: PackagingStructure
    cost_estimate: PackagingCost
    derivative_ideas: list[str] = Field(min_length=2, max_length=5)
    fact_refs: list[Citation] = Field(min_length=1, max_length=4)
    demo: bool = False
    fallback_reason: str | None = None

    @field_validator("palette")
    @classmethod
    def _palette_hex(cls, value: list[str]) -> list[str]:
        if any(not HEX_COLOR.match(item) for item in value):
            raise ValueError("palette 必须是 6 位十六进制颜色，如 #B6402A")
        return value


class Xiaohongshu(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=4, max_length=30)
    body: str = Field(min_length=30, max_length=700)
    tags: list[str] = Field(min_length=3, max_length=8)
    cover_text: str = Field(min_length=2, max_length=12)


class Douyin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: str = Field(min_length=4, max_length=60)
    script: str = Field(min_length=30, max_length=600)
    shots: list[str] = Field(min_length=3, max_length=6)


class Wechat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=4, max_length=30)
    body: str = Field(min_length=30, max_length=700)


class QA(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str = Field(min_length=2, max_length=60)
    a: str = Field(min_length=2, max_length=240)


class KolBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: str = Field(min_length=2, max_length=80)
    rationale: str = Field(min_length=5, max_length=200)
    message: str = Field(min_length=5, max_length=300)
    deliverables: list[str] = Field(min_length=2, max_length=5)


class MarketingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    xiaohongshu: Xiaohongshu
    douyin: Douyin
    wechat: Wechat
    cs_qa: list[QA] = Field(min_length=3, max_length=6)
    kol_brief: KolBrief
    fact_refs: list[Citation] = Field(min_length=1, max_length=4)
    demo: bool = False
    fallback_reason: str | None = None


class PriceTier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str = Field(min_length=2, max_length=30)
    pack: str = Field(min_length=2, max_length=40)
    price_per_kg: float = Field(gt=0, le=1000)
    price_total: float = Field(gt=0, le=10000)
    margin: float = Field(ge=-1, le=1)
    note: str = Field(min_length=2, max_length=120)


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step: str = Field(min_length=2, max_length=20)
    note: str = Field(min_length=2, max_length=120)


class PricingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_ladder: list[PriceTier] = Field(min_length=3, max_length=5)
    premium_pct: float = Field(ge=-100, le=2000)
    rationale: str = Field(min_length=30, max_length=600)
    formula: str = Field(min_length=20, max_length=500)
    cost_breakdown: dict[str, float]
    trace_timeline: list[TraceEvent] = Field(min_length=4, max_length=8)
    qr_payload: str = Field(min_length=4, max_length=300)
    persona_greeting: str = Field(min_length=5, max_length=160)
    faq: list[QA] = Field(min_length=2, max_length=6)
    fact_refs: list[Citation] = Field(min_length=1, max_length=3)
    is_demo: bool = True
    narrative_source: Literal["llm", "template"] = "template"
    demo: bool = False
    fallback_reason: str | None = None


class PricingNarrative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rationale: str = Field(min_length=30, max_length=600)
    persona_greeting: str = Field(min_length=5, max_length=160)
    faq: list[QA] = Field(min_length=2, max_length=6)


OUTPUT_MODELS: dict[AgentName, type[BaseModel]] = {
    AgentName.STORY: StoryOutput,
    AgentName.PACKAGING: PackagingOutput,
    AgentName.MARKETING: MarketingOutput,
    AgentName.PRICING: PricingOutput,
}


def validate_output(agent: AgentName, data: dict) -> BaseModel:
    return OUTPUT_MODELS[agent].model_validate(data)


def citations_for(data: dict) -> list[dict]:
    citations = data.get("cultural_evidence") or data.get("fact_refs") or []
    return [item for item in citations if isinstance(item, dict)]
