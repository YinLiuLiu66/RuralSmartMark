from pathlib import Path

from sqlalchemy import select

from ruralsmartmark.models import KnowledgeDoc
from ruralsmartmark.seed import seed_demo
from ruralsmartmark.services.knowledge import (
    load_markdown_docs,
    parse_markdown_document,
    resolve_knowledge_dir,
)


def test_markdown_docs_have_sources_and_unique_ids():
    directory = resolve_knowledge_dir("data/knowledge/zhaotong")
    docs = load_markdown_docs(directory)

    assert len(docs) == 10
    assert len({doc.doc_key for doc in docs}) == 10
    for doc in docs:
        assert doc.source_date.startswith("2026-10-")
        if doc.credibility == "demo":
            assert doc.source_url.startswith("internal://")
        else:
            assert doc.source_url.startswith("http")
            assert "TODO" not in doc.source_url


def test_frontmatter_rejects_missing_fields(tmp_path: Path):
    path = tmp_path / "bad.md"
    raw = "---\nid: X-01\ntitle: 缺字段\n---\n正文正文正文正文"
    try:
        parse_markdown_document(raw, path=path)
    except ValueError as exc:
        assert "缺少字段" in str(exc)
    else:
        raise AssertionError("缺字段的文档应报错")


async def test_seed_upserts_knowledge(session):
    await seed_demo(session)
    await seed_demo(session)

    docs = list(
        (await session.execute(select(KnowledgeDoc).order_by(KnowledgeDoc.doc_key))).scalars().all()
    )
    assert len(docs) == 10
    assert any(doc.doc_key == "GI-01" and doc.source_url.startswith("http") for doc in docs)
    assert any(doc.credibility == "demo" for doc in docs)


async def test_knowledge_endpoint(client, session):
    await seed_demo(session)
    response = await client.get("/api/knowledge")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 10
    assert any(
        doc["doc_key"] == "PRICE-01" and doc["source_url"].startswith("http") for doc in docs
    )
