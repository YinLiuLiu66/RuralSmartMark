from sqlalchemy import select

from ruralsmartmark.models import Batch, Benchmark, KnowledgeDoc, ProductProfile
from ruralsmartmark.schemas import (
    ResearchBenchmarkDraft,
    ResearchDocDraft,
    ResearchDraft,
    ResearchProduct,
)
from ruralsmartmark.services.products import commit_research_draft


def _draft(slug: str, name: str, prefix: str) -> ResearchDraft:
    doc = ResearchDocDraft(
        doc_id="ORIGIN-01",
        title="产地",
        type="产区",
        source_url="internal://test",
        source_date="2026-10-22",
        credibility="demo",
        content="这是测试用产地说明，仅用于验证多产品知识库。",
    )
    return ResearchDraft(
        product=ResearchProduct(
            slug=slug,
            name=name,
            county="测试县",
            province="测试省",
            category="鲜果",
            form="1kg 礼盒",
            palette={"apple": "#B6402A", "leaf": "#3F6B4F"},
        ),
        specs={
            "brand_name": f"{name}品牌",
            "ip_name": "测试守园人",
            "trace_prefix": prefix,
            "batch_prefix": prefix,
        },
        docs=[doc],
        benchmarks=[
            ResearchBenchmarkDraft(
                channel="散装批发",
                competitor=name,
                spec="1kg",
                price_per_kg=10,
                source_url="internal://test",
                source_date="2026-10-22",
            ),
            ResearchBenchmarkDraft(
                channel="电商散装",
                competitor=name,
                spec="1kg",
                price_per_kg=12,
                source_url="internal://test",
                source_date="2026-10-22",
            ),
            ResearchBenchmarkDraft(
                channel="品牌礼盒",
                competitor=name,
                spec="1kg",
                price_per_kg=25,
                source_url="internal://test",
                source_date="2026-10-22",
            ),
        ],
    )


async def test_two_products_can_reuse_doc_keys(session):
    first, first_batch, docs_a, _ = await commit_research_draft(
        session, _draft("alpha-fruit", "甲方水果", "AF")
    )
    second, second_batch, docs_b, _ = await commit_research_draft(
        session, _draft("beta-fruit", "乙方水果", "BF")
    )
    await session.commit()

    assert docs_a == 3
    assert docs_b == 3
    assert first.id != second.id
    assert first_batch.code.startswith("AF-")
    assert second_batch.code.startswith("BF-")

    rows = list(
        (
            await session.execute(
                select(KnowledgeDoc).where(KnowledgeDoc.doc_key == "ORIGIN-01")
            )
        )
        .scalars()
        .all()
    )
    assert {row.product_id for row in rows} == {first.id, second.id}

    products = list((await session.execute(select(ProductProfile))).scalars().all())
    assert {item.slug for item in products} == {"alpha-fruit", "beta-fruit"}
    benchmarks = list(
        (await session.execute(select(Benchmark).where(Benchmark.product_id == second.id)))
        .scalars()
        .all()
    )
    assert {item.channel for item in benchmarks} == {"散装批发", "电商散装", "品牌礼盒"}

    batches = list((await session.execute(select(Batch))).scalars().all())
    assert len(batches) == 2
