from sqlalchemy import select

from ruralsmartmark.models import Batch, Benchmark, KnowledgeDoc, ProductProfile
from ruralsmartmark.schemas import (
    ResearchBenchmarkDraft,
    ResearchDocDraft,
    ResearchDraft,
    ResearchProduct,
)
from ruralsmartmark.services.products import apply_user_inputs, commit_research_draft


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


def _user_draft(slug: str, name: str, **kwargs) -> ResearchDraft:
    return ResearchDraft(
        product=ResearchProduct(
            slug=slug,
            name=name,
            county="测试县",
            province="测试省",
            category="鲜果",
            form="1kg 礼盒",
        ),
        **kwargs,
    )


async def test_apply_user_inputs_merges_cost_assumptions(session):
    product, _, _, _ = await commit_research_draft(
        session, _draft("gamma-fruit", "丙方水果", "GF")
    )
    await session.commit()

    first = await apply_user_inputs(
        session,
        product,
        _user_draft(
            "gamma-fruit",
            "丙方水果",
            specs={
                "cost_assumptions": {
                    "loss_rate": 0.03,
                    "cold_chain_per_kg": 1.6,
                    "basis": "本地冷库报价",
                }
            },
        ),
    )
    await session.refresh(product)
    assert first["cost_assumptions"]["loss_rate"] == 0.03
    assert first["benchmarks"] == 0

    await apply_user_inputs(
        session,
        product,
        _user_draft(
            "gamma-fruit", "丙方水果", specs={"cost_assumptions": {"box_cost": 6.2}}
        ),
    )
    await session.refresh(product)
    costs = product.specs["cost_assumptions"]
    assert costs["box_cost"] == 6.2
    assert costs["loss_rate"] == 0.03
    assert costs["basis"] == "本地冷库报价"
    assert product.specs["brand_name"] == "丙方水果品牌"


async def test_apply_user_inputs_replaces_benchmarks_only_when_given(session):
    product, _, _, _ = await commit_research_draft(
        session, _draft("delta-fruit", "丁方水果", "DF")
    )
    await session.commit()

    await apply_user_inputs(
        session,
        product,
        _user_draft(
            "delta-fruit",
            "丁方水果",
            benchmarks=[
                ResearchBenchmarkDraft(
                    channel="散装批发",
                    competitor="丁方水果",
                    spec="1kg",
                    price_per_kg=9.0,
                    source_url="internal://user/price",
                    source_date="2026-11-08",
                )
            ],
        ),
    )

    rows = list(
        (await session.execute(select(Benchmark).where(Benchmark.product_id == product.id)))
        .scalars()
        .all()
    )
    assert [row.price_per_kg for row in rows] == [9.0]
