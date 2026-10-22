"""Demo seed for the first case (Zhaotong ugly apple)."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.base import AgentName
from ..agents.engine import _guard_allowed_numbers
from ..config import get_settings
from ..models import (
    AgentRun,
    Artifact,
    Batch,
    Benchmark,
    ChatMessage,
    ProductProfile,
    ScanEvent,
)
from ..services.fact_guard import check_output
from ..services.knowledge import list_knowledge_docs, upsert_knowledge_docs
from ..services.pricing import calculate_pricing

PRODUCT_SLUG = "zhaotong-ugly-apple"
DEMO_BATCH_CODE = "ZT-DEMO-001"
DEMO_TRACE_CODE = "ZTDEMO26"
PRICE_SOURCE = "https://www.cnhnb.com/p/pingguo/"

PRODUCT_SPECS = {
    "brand_name": "乌蒙丑果",
    "ip_name": "山风守园人",
    "origin": "云南省昭通市昭阳区",
    "fruit_size": "80-85mm",
    "pack": "5kg / 12 枚礼盒",
    "sugar": "可溶性固形物≥15.0%（地理标志登记资料）",
    "harvest": "晚熟红富士，秋季采摘",
    "altitude": "高海拔（具体数值待核验）",
    "positioning": "虚构合作社子品牌「乌蒙丑果」与 IP「山风守园人」；区域事实可查，品牌与人物为演示合成",
}

PRODUCT_PALETTE = {
    "apple": "#B6402A",
    "leaf": "#3F6B4F",
    "kraft": "#C9A46A",
    "paper": "#F7F3EA",
}

BENCHMARKS = [
    {
        "channel": "散装批发",
        "competitor": "昭通丑苹果 80-85mm",
        "spec": "10 斤/箱",
        "price_per_kg": 10.0,
        "source_url": PRICE_SOURCE,
        "source_date": "2026-10-21",
        "note": "演示测算：公开报价区间 2.8–8.7 元/斤，取 5 元/斤作精选果基线",
    },
    {
        "channel": "电商散装",
        "competitor": "昭通丑苹果 80-85mm",
        "spec": "5 斤/箱",
        "price_per_kg": 12.0,
        "source_url": PRICE_SOURCE,
        "source_date": "2026-10-21",
        "note": "演示测算：在散装基线上加分级与电商包装",
    },
    {
        "channel": "品牌礼盒",
        "competitor": "演示合作社礼盒",
        "spec": "5kg / 12 枚",
        "price_per_kg": 25.6,
        "source_url": PRICE_SOURCE,
        "source_date": "2026-10-21",
        "note": "128 元/5kg，演示目标价，不是公开成交价",
    },
]

DEMO_SNAPSHOT_FILE = Path(__file__).with_name("demo_batch.json")
DEMO_ILLUSTRATION_FILE = Path(__file__).with_name("demo_illustration.png")

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


async def _seed_knowledge(session: AsyncSession, product: ProductProfile) -> None:
    await upsert_knowledge_docs(session, product.id, product.knowledge_dir)


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


async def _seed_demo_snapshot(
    session: AsyncSession,
    product: ProductProfile,
    *,
    public_base_url: str,
    artifact_dir: Path | None = None,
) -> None:
    demo = await session.scalar(select(Batch).where(Batch.code == DEMO_BATCH_CODE))
    if demo is None:
        return

    now = datetime.now(UTC)
    runs: dict[AgentName, AgentRun] = {}

    if demo.story_json is None:
        snapshot = json.loads(DEMO_SNAPSHOT_FILE.read_text(encoding="utf-8"))
        story = snapshot["story"]
        packaging = snapshot["packaging"]
        marketing = snapshot["marketing"]

        docs = await list_knowledge_docs(session, product.id)
        benchmarks = list(
            (
                await session.execute(
                    select(Benchmark)
                    .where(Benchmark.product_id == product.id)
                    .order_by(Benchmark.id)
                )
            )
            .scalars()
            .all()
        )
        pricing = calculate_pricing(
            product,
            demo,
            packaging,
            benchmarks,
            docs,
            public_base_url=public_base_url,
            story=story,
            trace_code=DEMO_TRACE_CODE,
        )

        demo.story_json = story
        demo.packaging_json = packaging
        demo.marketing_json = marketing
        demo.pricing_json = pricing
        demo.state = "traced"
        demo.current_station = "trace"
        demo.trace_code = DEMO_TRACE_CODE
        await session.flush()

        for agent, data in (
            (AgentName.STORY, story),
            (AgentName.PACKAGING, packaging),
            (AgentName.MARKETING, marketing),
            (AgentName.PRICING, pricing),
        ):
            guard = check_output(
                data,
                docs,
                allowed_numbers=_guard_allowed_numbers(agent, product, demo, docs, data),
            )
            run = AgentRun(
                batch_id=demo.id,
                agent=agent.value,
                status="approved",
                input_json={"provider": "seed-snapshot"},
                output_json=data,
                guard_json=guard.as_dict(),
                model="seed-snapshot",
                tokens=0,
                started_at=now,
                finished_at=now,
            )
            session.add(run)
            await session.flush()
            runs[agent] = run
            session.add(
                Artifact(
                    batch_id=demo.id,
                    agent_run_id=run.id,
                    kind=agent.value,
                    content_json=data,
                    file_path=None,
                    approved_at=now,
                )
            )
    else:
        packaging = demo.packaging_json or {}

    if artifact_dir is None or not DEMO_ILLUSTRATION_FILE.is_file():
        return
    existing = await session.scalar(
        select(Artifact).where(
            Artifact.batch_id == demo.id,
            Artifact.kind == "illustration",
        )
    )
    if existing is not None:
        return

    prompt = str(packaging.get("ip_image_prompt") or "").strip()
    if not prompt:
        return
    packaging_run = runs.get(AgentName.PACKAGING)
    if packaging_run is None:
        packaging_run = await session.scalar(
            select(AgentRun)
            .where(AgentRun.batch_id == demo.id, AgentRun.agent == AgentName.PACKAGING.value)
            .order_by(AgentRun.id.desc())
        )

    target = artifact_dir / f"batch-{demo.id}" / "illustration-demo.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DEMO_ILLUSTRATION_FILE, target)
    session.add(
        Artifact(
            batch_id=demo.id,
            agent_run_id=packaging_run.id if packaging_run else None,
            kind="illustration",
            content_json={
                "prompt": prompt,
                "model": "Tongyi-MAI/Z-Image-Turbo",
                "demo": True,
                "source": "seed-snapshot",
            },
            file_path=str(target),
            approved_at=now,
        )
    )


async def seed_demo(
    session: AsyncSession,
    *,
    reset: bool = False,
    public_base_url: str | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, int]:
    """Idempotent seed; reset clears batches and their children but keeps product/docs/benchmarks."""
    product = await _upsert_product(session)
    await _seed_knowledge(session, product)
    await _seed_benchmarks(session, product.id)
    await _seed_batches(session, product.id, reset=reset)
    await session.flush()
    await _seed_demo_snapshot(
        session,
        product,
        public_base_url=public_base_url or get_settings().public_base_url,
        artifact_dir=artifact_dir,
    )
    await session.commit()
    return {"products": 1, "batches": len(BATCHES)}
