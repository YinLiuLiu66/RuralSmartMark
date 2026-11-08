from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pydantic import ValidationError
from pydantic_ai import Agent, RunContext
from pydantic_ai.settings import ModelSettings
from pydantic_ai.usage import UsageLimits

from ..config import Settings
from ..providers.search import ScrapedSource, SearchProvider
from ..schemas import CostAssumptions, ResearchDraft
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
        if doc.source_url.startswith("internal://user"):
            # 用户口述的事实没有可抓取原文，不做逐字校验，但要留痕并标未核验。
            doc.credibility = "user"
            warnings.append(f"{doc.doc_id} 由用户提供，未经外部核验")
            docs.append(doc)
            seen.add(doc.doc_id)
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


def _prepare_draft(draft: ResearchDraft, *, placeholders: bool = True) -> ResearchDraft:
    draft.product.slug = _slug(draft.product.slug)
    specs = dict(draft.specs or {})
    if placeholders:
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


def _load_draft(text: str) -> ResearchDraft:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        return ResearchDraft.model_validate_json(text)
    except Exception as exc:
        raise ResearchUnavailable(f"草案 JSON 解析失败：{str(exc)[:240]}") from exc


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
            "最多搜索 2 次；抓取只调用 1–2 次 scrape_sources，一次传 2–4 个 URL，不要逐页调用。"
            "抓取上限或搜索上限提示出现后，立即根据已有正文输出 JSON，不再调用工具。"
            "最后只输出一个 JSON 对象（不要 Markdown 代码围栏），结构必须符合给定 Schema。"
        ),
    )

    @agent.tool
    async def search_web(ctx: RunContext[ResearchDeps], query: str) -> list[dict]:
        """Search the web for candidate sources."""
        if len(ctx.deps.search_queries) >= 3:
            return [{"error": "搜索次数已达上限，请直接根据已有来源输出 JSON 草案。"}]
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
        if remaining <= 0:
            return [{"error": "抓取页数已达上限，请直接根据已有正文输出 JSON 草案。"}]
        selected = [url for url in urls if url not in ctx.deps.scraped][:remaining]
        if not selected:
            return [{"error": "没有新的 URL 可抓取，请直接输出 JSON 草案。"}]
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

请先搜索 1–2 次，再一次抓取 2–4 个最可靠来源，最后只输出一个 JSON 对象。
来源优先：政府/协会/主流媒体 > 电商挂牌页；每条事实单独成 doc，source_date 用页面日期或 {_TODAY}。
不要逐页调用抓取工具；达到搜索/抓取上限后直接输出草案。

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

    return verify_draft(_prepare_draft(_load_draft(result.output)), deps.scraped)


RECORD_INSTRUCTIONS = (
    "你是「智农云链」的资料录入助手：不搜索、不抓取、不做算术。"
    "职责是把用户口述的产品事实、价格和成本口径整理成结构化草案，只记录用户明确给出的内容，"
    "缺失的写进 questions，绝不编造数字或认证。"
    "用户是在补充既有产品时，product 各字段原样沿用已知信息，不要改写名字、产地或 slug；"
    "specs 里只写用户这次明确给出的内容，不要复述已知规格，否则会把旧档案冲掉。"
    "三档价格写进 benchmarks（channel 只能是 散装批发 / 电商散装 / 品牌礼盒），"
    "source_url 用 internal://user/price，note 写明“用户提供的报价”。"
    "成本口径写进 specs.cost_assumptions，字段与取值范围："
    "bulk_price_per_kg 收购基准价(元/kg)、fruit_ratio 果价占基准价比例(0.1-2)、loss_rate 损耗率(0-0.3)、"
    "sorting_per_kg 分选人工(0-20 元/kg)、cold_chain_per_kg 冷链(0-20 元/kg)、"
    "ecommerce_pack_per_kg 电商箱(0-20 元/kg)、box_cost 礼盒单盒成本(0-300 元)、"
    "platform_rate 平台费率(0-0.3)、marketing_rate 营销费率(0-0.3)、basis 依据一句话。"
    "用户没提到的成本项直接省略该键，不要填默认值，也不要替用户换算单位。"
    "用户口述的事实写成 doc：source_url 用 internal://user/<序号>，credibility 填 user，content 用用户原话。"
    "questions 用用户能看懂的中文写，不要出现字段名或英文键。"
    "最后只输出一个 JSON 对象，不要 Markdown 代码围栏。"
)


async def run_record(
    brief: str, *, settings: Settings, known: dict | None = None
) -> ResearchDraft:
    """把用户提供的数据整理成草案；不依赖搜索 provider，离线也能用。"""
    if not settings.openai_api_key:
        raise ResearchUnavailable("没有 OPENAI_API_KEY，无法结构化用户数据。")

    model = build_pydantic_model(settings)
    agent = Agent(
        model,
        output_type=str,
        model_settings=ModelSettings(
            max_tokens=settings.research_max_tokens, temperature=0.1
        ),
        instructions=RECORD_INSTRUCTIONS,
    )
    prompt = f"""用户提供的内容：
{brief}

已知信息（JSON）：
{json.dumps(known or {}, ensure_ascii=False)}

只输出一个 JSON 对象。输出 JSON Schema：
{json.dumps(ResearchDraft.model_json_schema(), ensure_ascii=False)}"""
    try:
        result = await agent.run(prompt, usage_limits=UsageLimits(request_limit=3))
    except Exception as exc:
        raise ResearchUnavailable(f"录入解析失败：{str(exc)[:240]}") from exc

    draft = _load_draft(result.output)
    raw = (draft.specs or {}).get("cost_assumptions")
    if isinstance(raw, dict) and raw:
        try:
            CostAssumptions.model_validate(raw)
        except ValidationError as exc:
            raise ResearchUnavailable(f"成本口径超出允许范围：{str(exc)[:200]}") from exc
    return verify_draft(_prepare_draft(draft, placeholders=False), {})
