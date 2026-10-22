from sqlalchemy import select

from ruralsmartmark.models import ProductProfile
from ruralsmartmark.seed import seed_demo
from ruralsmartmark.services.fact_guard import check_output
from ruralsmartmark.services.knowledge import list_knowledge_docs, quote_containing


async def _docs(session):
    await seed_demo(session)
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == "zhaotong-ugly-apple")
    )
    assert product is not None
    return await list_knowledge_docs(session, product.id)


def _payload(docs, *, quote: str | None = None, text: str = "秋天来了，苹果慢慢长甜。"):
    doc = next(item for item in docs if item.doc_key == "ENV-02")
    return {
        "ip_name": "山风守园人",
        "story_long": text,
        "cultural_evidence": [
            {
                "doc_id": "ENV-02",
                "quote": quote or quote_containing(doc, "低纬度、高海拔"),
                "use": "产地背景",
            }
        ],
    }


async def test_citation_must_be_verbatim(session):
    docs = await _docs(session)

    good = check_output(_payload(docs), docs)
    assert good.passed
    assert good.checked_citations == 1

    bad = check_output(_payload(docs, quote="昭通苹果种在海拔 1950 米的坝子里"), docs)
    assert not bad.passed
    assert any(issue.rule == "CRIT-02" for issue in bad.errors)


async def test_banned_claims_are_errors(session):
    docs = await _docs(session)

    result = check_output(_payload(docs, text="这是有机认证苹果，能降血糖。"), docs)
    rules = {issue.rule for issue in result.errors}
    assert "COMP-02" in rules
    assert "COMP-03" in rules


async def test_demo_citation_is_warning_not_error(session):
    docs = await _docs(session)
    demo = next(item for item in docs if item.doc_key == "DEMO-01")
    payload = _payload(docs)
    payload["cultural_evidence"].append(
        {
            "doc_id": "DEMO-01",
            "quote": quote_containing(demo, "本项目的合作社"),
            "use": "演示边界",
        }
    )

    result = check_output(payload, docs)
    assert result.passed
    assert any(issue.rule == "DEMO-01" for issue in result.warnings)


async def test_unsourced_number_is_warning(session):
    docs = await _docs(session)

    result = check_output(_payload(docs, text="果园海拔 2345 米，昼夜温差 15℃。"), docs)
    assert result.passed
    assert any(issue.rule == "NUM-01" for issue in result.warnings)


async def test_geographic_indication_question_is_not_a_claim(session):
    docs = await _docs(session)
    payload = _payload(docs)
    payload["cs_qa"] = [
        {
            "q": "你们有地理标志授权吗？",
            "a": "没有。我们只把昭通苹果作为产地背景，不冒充区域公用品牌授权。",
        }
    ]

    result = check_output(payload, docs)
    assert result.passed


async def test_geographic_indication_claim_is_error(session):
    docs = await _docs(session)
    payload = _payload(docs)
    payload["cs_qa"] = [
        {"q": "产地是哪里？", "a": "我们已获得地理标志授权，是官方推荐的昭通苹果。"}
    ]

    result = check_output(payload, docs)
    assert not result.passed
    assert any(issue.rule == "COMP-06" for issue in result.errors)


async def test_unknown_doc_id_is_error(session):
    docs = await _docs(session)
    payload = _payload(docs)
    payload["cultural_evidence"][0]["doc_id"] = "NOPE-99"

    result = check_output(payload, docs)
    assert not result.passed
    assert any(issue.rule == "CRIT-01" for issue in result.errors)
