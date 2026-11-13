"""Demo seed for the first case (Zhaotong ugly apple)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
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
    ControllerMessage,
    ControllerSession,
    ProductProfile,
    ScanEvent,
)
from ..services.fact_guard import check_output
from ..services.knowledge import list_knowledge_docs, upsert_knowledge_docs
from ..services.pricing import calculate_pricing
from ..services.trace import DEMO_BATCH_CODE, DEMO_TRACE_CODE

PRODUCT_SLUG = "zhaotong-ugly-apple"
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
    "origin_aliases": ["昭通", "昭阳"],
    "trace_headline": "这箱苹果，\n从乌蒙山来。",
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

ZHAOTONG_RAW_BATCH_CODE = "ZT-2026-001"

BATCHES = [
    {
        "code": DEMO_BATCH_CODE,
        "quantity_kg": 500.0,
        "state": "traced",
        "current_station": "trace",
        "trace_code": DEMO_TRACE_CODE,
    },
    {
        "code": ZHAOTONG_RAW_BATCH_CODE,
        "quantity_kg": 300.0,
        "state": "raw",
        "current_station": "intake",
        "trace_code": None,
    },
]


@dataclass(frozen=True)
class ProductSeed:
    slug: str
    name: str
    county: str
    province: str
    category: str
    form: str
    specs: dict
    palette: dict
    scene_preset: str
    knowledge_dir: str
    benchmarks: list[dict]
    batches: list[dict]


ZHAOTONG_SEED = ProductSeed(
    slug=PRODUCT_SLUG,
    name="昭通丑苹果",
    county="云南省昭通市昭阳区",
    province="云南省",
    category="鲜果",
    form="5kg / 12 枚礼盒",
    specs=PRODUCT_SPECS,
    palette=PRODUCT_PALETTE,
    scene_preset="orchard",
    knowledge_dir="data/knowledge/zhaotong",
    benchmarks=BENCHMARKS,
    batches=BATCHES,
)

SEED_PRODUCTS_DIR = Path(__file__).with_name("products")


def majiang_seed() -> ProductSeed:
    """工作台第二个产品：麻江蓝莓，停在 raw，方便现场演示「换个产品也能跑」。"""
    folder = SEED_PRODUCTS_DIR / "majiang"
    data = json.loads((folder / "product.json").read_text(encoding="utf-8"))
    benchmarks = json.loads((folder / "benchmarks.json").read_text(encoding="utf-8"))
    specs = dict(data.get("specs") or {})
    specs.setdefault("batch_prefix", "MJ")
    return ProductSeed(
        slug=str(data["slug"]),
        name=str(data["name"]),
        county=str(data["county"]),
        province=str(data["province"]),
        category=str(data["category"]),
        form=str(data["form"]),
        specs=specs,
        palette=dict(data.get("palette") or PRODUCT_PALETTE),
        scene_preset=str(data.get("scene_preset") or "orchard"),
        knowledge_dir=str(folder / "knowledge"),
        benchmarks=benchmarks,
        batches=[
            {
                "code": "MJ-2026-001",
                "quantity_kg": 120.0,
                "state": "raw",
                "current_station": "intake",
                "trace_code": None,
            }
        ],
    )


def seed_products() -> list[ProductSeed]:
    return [ZHAOTONG_SEED, majiang_seed()]


async def _upsert_product(session: AsyncSession, seed: ProductSeed) -> ProductProfile:
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == seed.slug)
    )
    if product is None:
        product = ProductProfile(slug=seed.slug)
        session.add(product)

    product.name = seed.name
    product.county = seed.county
    product.province = seed.province
    product.category = seed.category
    product.form = seed.form
    product.specs = seed.specs
    product.palette = seed.palette
    product.scene_preset = seed.scene_preset
    product.knowledge_dir = seed.knowledge_dir
    product.is_active = True
    await session.flush()
    return product


async def _seed_knowledge(session: AsyncSession, product: ProductProfile) -> None:
    await upsert_knowledge_docs(session, product.id, product.knowledge_dir)


async def _seed_benchmarks(
    session: AsyncSession, product_id: int, benchmarks: list[dict]
) -> None:
    await session.execute(delete(Benchmark).where(Benchmark.product_id == product_id))
    for item in benchmarks:
        session.add(Benchmark(product_id=product_id, **item))


async def _reset_batches(session: AsyncSession) -> None:
    await session.execute(delete(ControllerMessage))
    await session.execute(delete(ControllerSession))
    await session.execute(delete(ChatMessage))
    await session.execute(delete(ScanEvent))
    await session.execute(delete(Artifact))
    await session.execute(delete(AgentRun))
    await session.execute(delete(Batch))


async def _seed_batches(
    session: AsyncSession, product_id: int, batches: list[dict]
) -> None:
    for item in batches:
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
    seeds = seed_products()
    if reset:
        await _reset_batches(session)

    products: list[ProductProfile] = []
    total_batches = 0
    for seed in seeds:
        product = await _upsert_product(session, seed)
        await _seed_knowledge(session, product)
        await _seed_benchmarks(session, product.id, seed.benchmarks)
        await _seed_batches(session, product.id, seed.batches)
        products.append(product)
        total_batches += len(seed.batches)
    await session.flush()
    await _seed_demo_snapshot(
        session,
        products[0],
        public_base_url=public_base_url or get_settings().public_base_url,
        artifact_dir=artifact_dir,
    )
    await session.commit()
    return {"products": len(products), "batches": total_batches}
