from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Artifact, Batch, KnowledgeDoc, ProductProfile, ScanEvent
from ..schemas import (
    TraceBatchOut,
    TraceEvidenceOut,
    TraceMarketingOut,
    TraceOut,
    TracePackagingCopy,
    TracePackagingOut,
    TracePriceTier,
    TracePricingOut,
    TraceProductOut,
    TraceQA,
    TraceStoryOut,
    TraceTimelineEvent,
    TraceXiaohongshu,
)
from .knowledge import list_knowledge_docs

DEMO_BATCH_CODE = "ZT-DEMO-001"

_TIMELINE_LABEL = {
    "story": "故事定稿",
    "packaging": "包装定稿",
    "marketing": "内容定稿",
    "pricing": "定价与溯源码",
}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _citations(*values: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for value in values:
        for item in value.get("cultural_evidence") or value.get("fact_refs") or []:
            if isinstance(item, dict) and item.get("doc_id") and item.get("quote"):
                found.append(item)
    return found


def _evidence(citations: list[dict[str, Any]], docs: list[KnowledgeDoc]) -> list[TraceEvidenceOut]:
    docs_by_key = {doc.doc_key: doc for doc in docs}
    seen: set[tuple[str, str]] = set()
    result: list[TraceEvidenceOut] = []
    for citation in citations:
        doc_id = str(citation["doc_id"])
        quote = str(citation["quote"])
        key = (doc_id, quote)
        if key in seen:
            continue
        seen.add(key)
        doc = docs_by_key.get(doc_id)
        if doc is None:
            continue
        result.append(
            TraceEvidenceOut(
                doc_id=doc.doc_key,
                title=doc.title,
                source_url=doc.source_url,
                source_date=doc.source_date,
                credibility=doc.credibility,
                quote=quote,
                use=str(citation.get("use") or "") or None,
            )
        )
    return result[:8]


def _timeline(
    batch: Batch,
    latest: dict[str, Artifact],
    story: dict,
    packaging: dict,
    marketing: dict,
    pricing: dict,
) -> list[TraceTimelineEvent]:
    events = [
        TraceTimelineEvent(
            step="批次建立",
            note=f"{batch.code} · {batch.quantity_kg:g} kg",
            at=batch.created_at,
        )
    ]
    notes = {
        "story": f"IP「{story.get('ip_name', '山风守园人')}」与故事定稿",
        "packaging": str(packaging.get("concept") or "包装定稿"),
        "marketing": str(_dict(marketing.get("xiaohongshu")).get("title") or "内容定稿"),
        "pricing": (f"溢价 {pricing.get('premium_pct', 0)}% · 溯源码 {batch.trace_code}"),
    }
    for kind in ("story", "packaging", "marketing", "pricing"):
        artifact = latest.get(kind)
        if artifact is None or artifact.approved_at is None:
            continue
        events.append(
            TraceTimelineEvent(
                step=_TIMELINE_LABEL[kind],
                note=notes[kind],
                at=artifact.approved_at,
            )
        )
    return events


async def load_trace(session: AsyncSession, code: str) -> TraceOut | None:
    normalized = code.strip().upper()
    if not normalized:
        return None
    batch = await session.scalar(
        select(Batch).where(
            func.upper(Batch.trace_code) == normalized,
            Batch.state == "traced",
        )
    )
    if batch is None or not batch.trace_code:
        return None
    if not (
        batch.story_json and batch.packaging_json and batch.marketing_json and batch.pricing_json
    ):
        return None

    product = await session.get(ProductProfile, batch.product_id)
    if product is None:
        return None

    story = _dict(batch.story_json)
    packaging = _dict(batch.packaging_json)
    marketing = _dict(batch.marketing_json)
    pricing = _dict(batch.pricing_json)

    docs = await list_knowledge_docs(session, product.id)
    artifacts = list(
        (
            await session.execute(
                select(Artifact)
                .where(Artifact.batch_id == batch.id, Artifact.approved_at.is_not(None))
                .order_by(Artifact.approved_at, Artifact.id)
            )
        )
        .scalars()
        .all()
    )
    latest: dict[str, Artifact] = {}
    for artifact in artifacts:
        latest[artifact.kind] = artifact

    scan_count = int(
        await session.scalar(
            select(func.count()).select_from(ScanEvent).where(ScanEvent.batch_id == batch.id)
        )
        or 0
    )
    last_scanned_at = await session.scalar(
        select(func.max(ScanEvent.created_at)).where(ScanEvent.batch_id == batch.id)
    )

    specs = _dict(product.specs)
    brand_name = str(specs.get("brand_name") or "乌蒙丑果")
    ip_name = str(story.get("ip_name") or specs.get("ip_name") or "山风守园人")

    price_ladder = [
        TracePriceTier.model_validate(item)
        for item in pricing.get("price_ladder") or []
        if isinstance(item, dict)
    ]
    faq = [
        TraceQA.model_validate(item) for item in pricing.get("faq") or [] if isinstance(item, dict)
    ]
    xiaohongshu = _dict(marketing.get("xiaohongshu"))
    douyin = _dict(marketing.get("douyin"))
    wechat = _dict(marketing.get("wechat"))
    packaging_copy = _dict(packaging.get("packaging_copy"))
    structure = packaging.get("structure") or {}
    if not isinstance(structure, dict):
        structure = {}
    journey = [
        TraceTimelineEvent(step=str(item.get("step", "")), note=str(item.get("note", "")))
        for item in pricing.get("trace_timeline") or []
        if isinstance(item, dict)
    ]

    return TraceOut(
        trace_code=batch.trace_code,
        batch=TraceBatchOut(
            code=batch.code,
            trace_code=batch.trace_code,
            quantity_kg=batch.quantity_kg,
            created_at=batch.created_at,
        ),
        product=TraceProductOut(
            name=product.name,
            county=product.county,
            province=product.province,
            form=product.form,
            brand_name=brand_name,
            ip_name=ip_name,
            specs=specs,
        ),
        story=TraceStoryOut(
            ip_name=ip_name,
            persona=str(story.get("persona") or ""),
            story_long=str(story.get("story_long") or ""),
            story_short=str(story.get("story_short") or ""),
            taglines=[str(item) for item in story.get("taglines") or []],
            evidence=_evidence(_citations(story, packaging, pricing), docs),
        ),
        packaging=TracePackagingOut(
            concept=str(packaging.get("concept") or ""),
            packaging_copy=TracePackagingCopy(
                front=str(packaging_copy.get("front") or ""),
                back=str(packaging_copy.get("back") or ""),
                side=str(packaging_copy.get("side") or ""),
                inside=str(packaging_copy.get("inside") or ""),
            ),
            structure={str(key): str(value) for key, value in structure.items()},
            image_url=f"/api/trace/{batch.trace_code}/packaging.png",
        ),
        marketing=TraceMarketingOut(
            xiaohongshu=TraceXiaohongshu(
                title=str(xiaohongshu.get("title") or ""),
                body=str(xiaohongshu.get("body") or ""),
                tags=[str(item) for item in xiaohongshu.get("tags") or []],
                cover_text=str(xiaohongshu.get("cover_text") or ""),
            ),
            douyin_hook=str(douyin.get("hook") or ""),
            wechat_title=str(wechat.get("title") or ""),
        ),
        pricing=TracePricingOut(
            price_ladder=price_ladder,
            premium_pct=float(pricing.get("premium_pct") or 0),
            rationale=str(pricing.get("rationale") or ""),
            formula=str(pricing.get("formula") or ""),
            cost_breakdown={
                str(key): float(value)
                for key, value in _dict(pricing.get("cost_breakdown")).items()
            },
            faq=faq,
            persona_greeting=str(pricing.get("persona_greeting") or ""),
            is_demo=bool(pricing.get("is_demo", True)),
        ),
        timeline=_timeline(batch, latest, story, packaging, marketing, pricing),
        journey=journey,
        scan_count=scan_count,
        last_scanned_at=last_scanned_at,
        demo=bool(pricing.get("is_demo", True)),
        fixed_demo=batch.code == DEMO_BATCH_CODE,
    )
