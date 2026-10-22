from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from ..config import Settings
from ..providers.search import ScrapedSource, SearchProvider
from ..schemas import ResearchDraft
from .pydantic_model import build_pydantic_model

_TODAY = datetime.now(UTC).date().isoformat()


class ResearchUnavailable(RuntimeError):
    """调研服务无法启动（没有 LLM key 或搜索 provider 不可用）。"""


@dataclass(slots=True)
class ResearchDeps:
    search: SearchProvider
    settings: Settings
    scraped: dict[str, ScrapedSource] = field(default_factory=dict)
    search_queries: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or f"product-{datetime.now(UTC).strftime('%Y%m%d%H%M')}"


def _source_date(value: str) -> str:
    return value if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") else _TODAY


def verify_draft(draft: ResearchDraft, scraped: dict[str, ScrapedSource]) -> ResearchDraft:
    """Drop any quote that is not literally present in its scraped source."""
    warnings = list(draft.warnings)
    docs = []
    seen: set[str] = set()
    for doc in draft.docs:
        if doc.doc_id in seen:
            warnings.append(f"重复 doc_id 已丢弃：{doc.doc_id}")
            continue
        if doc.source_url.startswith("internal://"):
            docs.append(doc)
            seen.add(doc.doc_id)
            continue
        page = scraped.get(doc.source_url)
        if page is None:
            warnings.append(f"来源未抓取，已丢弃：{doc.doc_id} / {doc.source_url}")
            continue
        if _normalize(doc.content) not in _normalize(page.markdown):
            warnings.append(f"引用未逐字命中页面，已丢弃：{doc.doc_id}")
            continue
        doc.source_date = _source_date(doc.source_date)
        docs.append(doc)
        seen.add(doc.doc_id)

    draft.docs = docs
    draft.warnings = warnings
    if not docs:
        draft.questions.append("我还没有拿到可逐字引用的来源；请补充官网/报道链接或原文。")
    return draft


def _prepare_draft(draft: ResearchDraft) -> ResearchDraft:
    draft.product.slug = _slug(draft.product.slug)
    specs = dict(draft.specs or {})
    if not specs.get("brand_name"):
        specs["brand_name"] = f"{draft.product.name}演示品牌"
        draft.warnings.append("品牌名未提供，暂用演示占位，可在对话里改。")
    if not specs.get("ip_name"):
        specs["ip_name"] = "山野记录者"
        draft.warnings.append("IP 名未提供，暂用演示占位，可在对话里改。")
    specs.setdefault("origin", draft.product.county)
    specs.setdefault("pack", draft.product.form)
    specs.setdefault("positioning", "虚构合作社子品牌；品牌、角色与批次数据为演示合成")
    specs.setdefault("trace_prefix", "PR")
    specs.setdefault("batch_prefix", specs["trace_prefix"])
    draft.specs = specs
    return draft


async def run_research(
    brief: str,
    *,
    settings: Settings,
    search: SearchProvider,
    known: dict | None = None,
) -> ResearchDraft:
    if not settings.openai_api_key:
        raise ResearchUnavailable("没有 OPENAI_API_KEY，无法启动调研 Agent。")
    if search.name == "unavailable":
        raise ResearchUnavailable(
            "没有配置 Firecrawl；请填 FIRECRAWL_API_KEY，或直接粘贴来源链接/原文。"
        )

    model = build_pydantic_model(settings)
    agent = Agent(
        model,
        output_type=str,
        deps_type=ResearchDeps,
        model_settings=ModelSettings(
            max_tokens=settings.research_max_tokens,
            temperature=0.4,
        ),
        instructions=(
            "你是县域农产品品牌调研 Agent。先判断已知信息，再用工具搜索和抓取来源。"
            "只能引用抓取正文里逐字出现的句子；不要编年份、认证、产量、人物或价格。"
            "每个 doc 的 content 必须是从某一页抓取正文复制的原句/原段，source_url 必须对应那页。"
            "缺失的品牌/IP、包装规格、三档价格写进 questions，不要硬凑。"
            "最后只输出一个 JSON 对象（不要 Markdown 代码围栏），结构必须符合给定 Schema。"
        ),
    )

    @agent.tool
    async def search_web(ctx: RunContext[ResearchDeps], query: str) -> list[dict]:
        """Search the web for candidate sources."""
        hits = await ctx.deps.search.search(
            query, limit=ctx.deps.settings.search_max_results
        )
        ctx.deps.search_queries.append(query)
        return [
            {"title": hit.title, "url": hit.url, "description": hit.description}
            for hit in hits
        ]

    @agent.tool
    async def scrape_sources(ctx: RunContext[ResearchDeps], urls: list[str]) -> list[dict]:
        """Fetch up to four pages as Markdown and return excerpts."""
        remaining = ctx.deps.settings.search_max_scrapes - len(ctx.deps.scraped)
        selected = [url for url in urls if url not in ctx.deps.scraped][: max(0, remaining)]
        results: list[dict] = []
        for url in selected:
            try:
                page = await ctx.deps.search.scrape(url)
            except Exception as exc:  # noqa: BLE001 - 单页失败不终止整轮
                results.append({"url": url, "error": str(exc)[:200]})
                continue
            ctx.deps.scraped[url] = page
            results.append(
                {
                    "url": url,
                    "title": page.title,
                    "markdown": page.markdown[:8000],
                }
            )
        return results

    known_text = "\n".join(f"{key}: {value}" for key, value in (known or {}).items())
    prompt = f"""用户对新产品的初始描述：
{brief}

已知字段：
{known_text or "（无）"}

请先搜索，再抓取 2–4 个最可靠来源，最后只输出一个 JSON 对象。
来源优先：政府/协会/主流媒体 > 电商挂牌页；每条事实单独成 doc，source_date 用页面日期或 {_TODAY}。

输出 JSON Schema：
{json.dumps(ResearchDraft.model_json_schema(), ensure_ascii=False)}"""
    deps = ResearchDeps(search=search, settings=settings)
    try:
        result = await agent.run(
            prompt,
            deps=deps,
            usage_limits=UsageLimits(
                request_limit=settings.research_request_limit,
                tool_calls_limit=settings.research_tool_calls_limit,
            ),
        )
    except Exception as exc:
        raise ResearchUnavailable(f"调研 Agent 调用失败：{str(exc)[:240]}") from exc

    text = result.output.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        draft = ResearchDraft.model_validate_json(text)
    except Exception as exc:
        raise ResearchUnavailable(f"调研草案 JSON 解析失败：{str(exc)[:240]}") from exc
    return verify_draft(_prepare_draft(draft), deps.scraped)
