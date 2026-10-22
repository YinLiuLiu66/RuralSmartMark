from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Batch, Benchmark, ProductProfile
from ..schemas import ResearchDraft
from .knowledge import KnowledgeDocument, upsert_knowledge_documents


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _boundary_docs(draft: ResearchDraft) -> list[KnowledgeDocument]:
    existing = {doc.doc_id for doc in draft.docs}
    docs: list[KnowledgeDocument] = []
    if "DEMO-01" not in existing:
        docs.append(
            KnowledgeDocument(
                doc_key="DEMO-01",
                title="项目演示边界",
                type="演示",
                source_url="internal://demo-boundary",
                source_date=_today(),
                publisher="智农云链",
                credibility="demo",
                content=(
                    "品牌、角色、合作社与批次数据均为演示合成。"
                    "所有价格、成本和溢价均为演示测算。"
                ),
            )
        )
    if "PRICE-01" not in existing:
        docs.append(
            KnowledgeDocument(
                doc_key="PRICE-01",
                title="价格基线口径",
                type="价格",
                source_url="internal://demo-price",
                source_date=_today(),
                publisher="智农云链",
                credibility="demo",
                content="演示测算采用公开挂牌价、用户输入与项目假设作基线，不代表真实成交价。",
            )
        )
    return docs


def _benchmark_defaults(draft: ResearchDraft) -> list[Benchmark]:
    present = {item.channel: item for item in draft.benchmarks}
    fallback = {
        "散装批发": 10.0,
        "电商散装": 12.0,
        "品牌礼盒": 25.6,
    }
    result: list[Benchmark] = []
    for channel, price in fallback.items():
        item = present.get(channel)
        if item is not None:
            result.append(
                Benchmark(
                    channel=item.channel,
                    competitor=item.competitor,
                    spec=item.spec,
                    price_per_kg=item.price_per_kg,
                    source_url=item.source_url or None,
                    source_date=item.source_date or None,
                    note=item.note or None,
                )
            )
        else:
            result.append(
                Benchmark(
                    channel=channel,
                    competitor=draft.product.name,
                    spec=draft.product.form,
                    price_per_kg=price,
                    source_url="internal://demo-price",
                    source_date=_today(),
                    note="未提供公开基准，使用演示假设，需人工确认",
                )
            )
    return result


async def _next_batch_code(session: AsyncSession, product: ProductProfile) -> str:
    year = datetime.now(UTC).year
    prefix = str((product.specs or {}).get("batch_prefix") or "ZT").strip() or "ZT"
    head = f"{prefix[:6]}-{year}-"
    count = await session.scalar(
        select(func.count()).select_from(Batch).where(Batch.code.like(f"{head}%"))
    )
    return f"{head}{int(count or 0) + 1:03d}"


async def commit_research_draft(
    session: AsyncSession,
    draft: ResearchDraft,
    *,
    quantity_kg: float = 300.0,
) -> tuple[ProductProfile, Batch, int, int]:
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == draft.product.slug)
    )
    if product is None:
        product = ProductProfile(slug=draft.product.slug)
        session.add(product)

    product.name = draft.product.name
    product.county = draft.product.county
    product.province = draft.product.province
    product.category = draft.product.category
    product.form = draft.product.form
    product.palette = draft.product.palette or product.palette or {}
    product.specs = draft.specs
    product.scene_preset = "orchard"
    product.knowledge_dir = ""
    product.is_active = True
    await session.flush()

    documents = [
        KnowledgeDocument(
            doc_key=doc.doc_id,
            title=doc.title,
            type=doc.type,
            source_url=doc.source_url,
            source_date=doc.source_date,
            publisher="",
            credibility=doc.credibility,
            content=doc.content,
        )
        for doc in draft.docs
    ]
    documents.extend(_boundary_docs(draft))
    doc_count = await upsert_knowledge_documents(session, product.id, documents)

    await session.execute(delete(Benchmark).where(Benchmark.product_id == product.id))
    benchmarks = _benchmark_defaults(draft)
    for item in benchmarks:
        item.product_id = product.id
        session.add(item)

    batch = Batch(
        product_id=product.id,
        code=await _next_batch_code(session, product),
        quantity_kg=quantity_kg,
        state="raw",
        current_station="intake",
    )
    session.add(batch)
    await session.flush()
    return product, batch, doc_count, len(benchmarks)
