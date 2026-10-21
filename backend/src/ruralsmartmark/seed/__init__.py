"""Demo seed for the first case (Zhaotong ugly apple)."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    AgentRun,
    Artifact,
    Batch,
    Benchmark,
    ChatMessage,
    KnowledgeDoc,
    ProductProfile,
    ScanEvent,
)

PRODUCT_SLUG = "zhaotong-ugly-apple"
DEMO_BATCH_CODE = "ZT-DEMO-001"
DEMO_TRACE_CODE = "ZTDEMO26"

PRODUCT_SPECS = {
    "origin": "云南省昭通市昭阳区",
    "fruit_size": "80-85mm",
    "pack": "5kg / 12 枚礼盒",
    "sugar": "可溶性固形物 14-15.7%（待核验）",
    "harvest": "晚熟红富士，秋季采摘（待核验）",
    "altitude": "1800-2500m，核心坝区约 1950m（待核验）",
    "positioning": "虚构合作社子品牌；区域事实可查，品牌与人物为演示合成",
}

PRODUCT_PALETTE = {
    "apple": "#B6402A",
    "leaf": "#3F6B4F",
    "kraft": "#C9A46A",
    "paper": "#F7F3EA",
}

KNOWLEDGE_DOCS = [
    {
        "doc_key": "GI-01",
        "title": "昭通苹果地理标志（待核验）",
        "type": "gi",
        "source_url": "TODO",
        "source_date": "2026-10-21",
        "content": "待核验：昭通苹果为国家地理标志保护产品；公告号、批准年份与保护范围待补。",
        "credibility": "todo",
    },
    {
        "doc_key": "ENV-01",
        "title": "昭通苹果产区与糖度（待核验）",
        "type": "origin",
        "source_url": "TODO",
        "source_date": "2026-10-21",
        "content": "待核验：核心产区为昭阳区，海拔约 1800-2500m，可溶性固形物约 14-15.7%。",
        "credibility": "todo",
    },
    {
        "doc_key": "PRICE-01",
        "title": "昭通丑苹果价格基准（待核验）",
        "type": "price",
        "source_url": "TODO",
        "source_date": "2026-10-21",
        "content": "待核验：散装约 3.5-6.2 元/斤，礼盒约 8.7-14.5 元/斤；仅作演示测算。",
        "credibility": "todo",
    },
]

BENCHMARKS = [
    {
        "channel": "散装批发",
        "competitor": "昭通丑苹果 80-85mm",
        "spec": "10 斤/箱",
        "price_per_kg": 10.0,
        "source_url": "TODO",
        "source_date": "2026-10-21",
        "note": "演示测算，公开报价待核验",
    },
    {
        "channel": "电商散装",
        "competitor": "昭通丑苹果 80-85mm",
        "spec": "5 斤/箱",
        "price_per_kg": 12.0,
        "source_url": "TODO",
        "source_date": "2026-10-21",
        "note": "演示测算，公开报价待核验",
    },
    {
        "channel": "品牌礼盒",
        "competitor": "演示合作社礼盒",
        "spec": "5kg / 12 枚",
        "price_per_kg": 25.6,
        "source_url": "TODO",
        "source_date": "2026-10-21",
        "note": "128 元/5kg，演示测算",
    },
]

BATCHES = [
    {
        "code": DEMO_BATCH_CODE,
        "quantity_kg": 500.0,
        "state": "traced",
        "current_station": "trace",
        "trace_code": DEMO_TRACE_CODE,
    },
    {
        "code": "ZT-2026-001",
        "quantity_kg": 300.0,
        "state": "raw",
        "current_station": "intake",
        "trace_code": None,
    },
]


async def _upsert_product(session: AsyncSession) -> ProductProfile:
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == PRODUCT_SLUG)
    )
    if product is None:
        product = ProductProfile(slug=PRODUCT_SLUG)
        session.add(product)

    product.name = "昭通丑苹果"
    product.county = "云南省昭通市昭阳区"
    product.province = "云南省"
    product.category = "鲜果"
    product.form = "5kg / 12 枚礼盒"
    product.specs = PRODUCT_SPECS
    product.palette = PRODUCT_PALETTE
    product.scene_preset = "orchard"
    product.knowledge_dir = "data/knowledge/zhaotong"
    product.is_active = True
    await session.flush()
    return product


async def _seed_knowledge(session: AsyncSession, product_id: int) -> None:
    for doc in KNOWLEDGE_DOCS:
        existing = await session.scalar(
            select(KnowledgeDoc).where(KnowledgeDoc.doc_key == doc["doc_key"])
        )
        if existing is None:
            existing = KnowledgeDoc(doc_key=doc["doc_key"], product_id=product_id)
            session.add(existing)
        existing.title = doc["title"]
        existing.type = doc["type"]
        existing.source_url = doc["source_url"]
        existing.source_date = doc["source_date"]
        existing.content = doc["content"]
        existing.credibility = doc["credibility"]


async def _seed_benchmarks(session: AsyncSession, product_id: int) -> None:
    await session.execute(delete(Benchmark).where(Benchmark.product_id == product_id))
    for item in BENCHMARKS:
        session.add(Benchmark(product_id=product_id, **item))


async def _seed_batches(session: AsyncSession, product_id: int, *, reset: bool) -> None:
    if reset:
        await session.execute(delete(ChatMessage))
        await session.execute(delete(ScanEvent))
        await session.execute(delete(Artifact))
        await session.execute(delete(AgentRun))
        await session.execute(delete(Batch))

    for item in BATCHES:
        existing = await session.scalar(select(Batch).where(Batch.code == item["code"]))
        if existing is None:
            session.add(Batch(product_id=product_id, **item))


async def seed_demo(session: AsyncSession, *, reset: bool = False) -> dict[str, int]:
    """Idempotent seed; reset clears batches and their children but keeps product/docs/benchmarks."""
    product = await _upsert_product(session)
    await _seed_knowledge(session, product.id)
    await _seed_benchmarks(session, product.id)
    await _seed_batches(session, product.id, reset=reset)
    await session.commit()
    return {"products": 1, "batches": len(BATCHES)}
