from ruralsmartmark.agents.research import verify_draft
from ruralsmartmark.providers.search import ScrapedSource
from ruralsmartmark.schemas import ResearchDocDraft, ResearchDraft, ResearchProduct


def _draft(content: str, url: str) -> ResearchDraft:
    return ResearchDraft(
        product=ResearchProduct(
            slug="test-fruit",
            name="测试水果",
            county="测试县",
            category="鲜果",
            form="1kg 礼盒",
        ),
        docs=[
            ResearchDocDraft(
                doc_id="ORIGIN-01",
                title="产地",
                type="产区",
                source_url=url,
                source_date="2026-10-22",
                credibility="media",
                content=content,
            )
        ],
    )


def test_quotes_must_match_scraped_page():
    page = ScrapedSource(
        url="https://example.com/source",
        title="来源",
        markdown="测试县位于山地，当地以鲜果闻名。附近有河。",
    )
    good = verify_draft(
        _draft("测试县位于山地，当地以鲜果闻名。", "https://example.com/source"),
        {page.url: page},
    )
    assert len(good.docs) == 1
    assert not good.warnings

    bad = verify_draft(
        _draft("测试县位于海边，当地以鲜果闻名。", "https://example.com/source"),
        {page.url: page},
    )
    assert bad.docs == []
    assert any("未逐字命中" in item for item in bad.warnings)
    assert bad.questions
