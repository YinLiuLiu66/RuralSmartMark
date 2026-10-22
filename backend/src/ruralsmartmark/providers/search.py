from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from ..config import Settings


class SearchUnavailable(RuntimeError):
    """搜索服务未配置或调用失败；由总控转成可操作提示。"""


@dataclass(slots=True)
class SearchHit:
    title: str
    url: str
    description: str = ""


@dataclass(slots=True)
class ScrapedSource:
    url: str
    title: str
    markdown: str
    published_time: str | None = None
    status_code: int | None = None


class SearchProvider(Protocol):
    name: str

    async def search(self, query: str, *, limit: int = 5) -> list[SearchHit]: ...

    async def scrape(self, url: str) -> ScrapedSource: ...


class UnavailableSearchProvider:
    name = "unavailable"

    async def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        raise SearchUnavailable(
            "未配置 Firecrawl；请在 backend/.env 填 FIRECRAWL_API_KEY，或直接粘贴来源链接/原文。"
        )

    async def scrape(self, url: str) -> ScrapedSource:
        raise SearchUnavailable(
            "未配置 Firecrawl；请在 backend/.env 填 FIRECRAWL_API_KEY，或直接粘贴来源链接/原文。"
        )


class FirecrawlSearchProvider:
    name = "firecrawl"

    def __init__(self, settings: Settings) -> None:
        from firecrawl import Firecrawl

        self._client = Firecrawl(
            api_key=settings.firecrawl_api_key,
            timeout=settings.search_timeout_seconds,
            max_retries=1,
        )

    async def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        try:
            result = await asyncio.to_thread(
                self._client.search,
                query,
                limit=limit,
                sources=["web"],
            )
        except Exception as exc:
            raise SearchUnavailable(f"Firecrawl 搜索失败：{str(exc)[:240]}") from exc

        hits: list[SearchHit] = []
        for item in getattr(result, "web", None) or []:
            url = str(getattr(item, "url", "") or "").strip()
            if not url:
                continue
            hits.append(
                SearchHit(
                    title=str(getattr(item, "title", "") or ""),
                    url=url,
                    description=str(getattr(item, "description", "") or ""),
                )
            )
        return hits[:limit]

    async def scrape(self, url: str) -> ScrapedSource:
        try:
            document = await asyncio.to_thread(
                self._client.scrape,
                url,
                formats=["markdown"],
                only_main_content=True,
            )
        except Exception as exc:
            raise SearchUnavailable(f"Firecrawl 抓取失败：{str(exc)[:240]}") from exc

        markdown = str(getattr(document, "markdown", "") or "").strip()
        if not markdown:
            raise SearchUnavailable(f"页面没有可用正文：{url}")
        metadata = getattr(document, "metadata", None)
        return ScrapedSource(
            url=url,
            title=str(getattr(metadata, "title", "") or ""),
            markdown=markdown,
            published_time=(
                str(getattr(metadata, "published_time", "") or "") or None
                if metadata is not None
                else None
            ),
            status_code=(
                int(getattr(metadata, "status_code", 0) or 0) or None
                if metadata is not None
                else None
            ),
        )


class MockSearchProvider:
    name = "mock"

    def __init__(
        self,
        hits: list[SearchHit] | None = None,
        pages: dict[str, ScrapedSource] | None = None,
    ) -> None:
        self._hits = hits or []
        self._pages = pages or {}

    async def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        return self._hits[:limit]

    async def scrape(self, url: str) -> ScrapedSource:
        page = self._pages.get(url)
        if page is None:
            raise SearchUnavailable(f"mock 没有页面：{url}")
        return page


def get_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "firecrawl" and settings.firecrawl_api_key:
        return FirecrawlSearchProvider(settings)
    return UnavailableSearchProvider()
