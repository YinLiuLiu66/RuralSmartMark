from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import BACKEND_DIR
from ..models import KnowledgeDoc

REQUIRED_META = ("id", "title", "type", "source_url", "source_date", "credibility")
_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


@dataclass(slots=True)
class KnowledgeDocument:
    doc_key: str
    title: str
    type: str
    source_url: str
    source_date: str
    publisher: str
    credibility: str
    content: str

    @property
    def is_demo(self) -> bool:
        return self.credibility == "demo"


def parse_markdown_document(raw: str, *, path: Path | None = None) -> KnowledgeDocument:
    match = _FRONTMATTER.match(raw.strip())
    if match is None:
        raise ValueError(f"知识库文档缺少 frontmatter: {path or '<memory>'}")

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"frontmatter 行无法解析: {line!r} ({path or '<memory>'})")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")

    missing = [key for key in REQUIRED_META if not meta.get(key)]
    if missing:
        raise ValueError(f"知识库文档缺少字段 {missing}: {path or '<memory>'}")

    content = match.group(2).strip()
    if len(content) < 10:
        raise ValueError(f"知识库正文过短: {path or '<memory>'}")

    return KnowledgeDocument(
        doc_key=meta["id"],
        title=meta["title"],
        type=meta["type"],
        source_url=meta["source_url"],
        source_date=meta["source_date"],
        publisher=meta.get("publisher", ""),
        credibility=meta["credibility"],
        content=content,
    )


def resolve_knowledge_dir(value: str) -> Path:
    path = Path(value)
    candidates = (
        [path]
        if path.is_absolute()
        else [
            BACKEND_DIR.parent / path,
            BACKEND_DIR / path,
            Path.cwd() / path,
        ]
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    raise FileNotFoundError(f"知识库目录不存在: {value}")


def load_markdown_docs(directory: Path) -> list[KnowledgeDocument]:
    docs: list[KnowledgeDocument] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.md")):
        doc = parse_markdown_document(path.read_text(encoding="utf-8"), path=path)
        if doc.doc_key in seen:
            raise ValueError(f"知识库 doc_id 重复: {doc.doc_key}")
        seen.add(doc.doc_key)
        docs.append(doc)
    if not docs:
        raise ValueError(f"知识库为空: {directory}")
    return docs


async def upsert_knowledge_documents(
    session: AsyncSession, product_id: int, docs: list[KnowledgeDocument]
) -> int:
    for doc in docs:
        existing = await session.scalar(
            select(KnowledgeDoc).where(
                KnowledgeDoc.product_id == product_id,
                KnowledgeDoc.doc_key == doc.doc_key,
            )
        )
        if existing is None:
            existing = KnowledgeDoc(doc_key=doc.doc_key, product_id=product_id)
            session.add(existing)
        existing.title = doc.title
        existing.type = doc.type
        existing.source_url = doc.source_url
        existing.source_date = doc.source_date
        existing.content = doc.content
        existing.credibility = doc.credibility
    await session.flush()
    return len(docs)


async def upsert_knowledge_docs(session: AsyncSession, product_id: int, knowledge_dir: str) -> int:
    directory = resolve_knowledge_dir(knowledge_dir)
    docs = load_markdown_docs(directory)
    return await upsert_knowledge_documents(session, product_id, docs)


async def list_knowledge_docs(session: AsyncSession, product_id: int) -> list[KnowledgeDoc]:
    result = await session.execute(
        select(KnowledgeDoc)
        .where(KnowledgeDoc.product_id == product_id)
        .order_by(KnowledgeDoc.doc_key)
    )
    return list(result.scalars().all())


def format_docs_for_prompt(docs: list[KnowledgeDoc]) -> str:
    blocks = []
    for doc in docs:
        blocks.append(
            f"[{doc.doc_key}] {doc.title}｜credibility={doc.credibility}｜"
            f"来源={doc.source_url}｜日期={doc.source_date}\n{doc.content}"
        )
    return "\n\n".join(blocks)


def quote_containing(doc: KnowledgeDoc, needle: str, *, max_len: int = 140) -> str:
    content = doc.content.replace("\n", " ").strip()
    index = content.find(needle)
    if index < 0:
        raise ValueError(f"知识库 {doc.doc_key} 中找不到引用片段: {needle}")

    left = max(content.rfind("。", 0, index) + 1, 0)
    right = content.find("。", index)
    right = len(content) if right < 0 else right + 1
    quote = content[left:right].strip()
    if len(quote) > max_len:
        quote = content[index : index + max_len].strip()
    return quote


def docs_number_tokens(docs: list[KnowledgeDoc]) -> set[str]:
    tokens: set[str] = set()
    for doc in docs:
        tokens.update(re.findall(r"\d+(?:\.\d+)?", doc.content))
    return tokens
