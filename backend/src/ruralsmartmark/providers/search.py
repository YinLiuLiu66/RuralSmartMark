from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar

from ..config import Settings

_T = TypeVar("_T")

_NETWORK_HINTS = (
    "ssl",
    "eof",
    "connection",
    "connect",
    "timeout",
    "timed out",
    "network",
    "temporarily",
    "502",
    "503",
    "504",
)


def _friendly_error(action: str, exc: BaseException) -> str:
    text = str(exc)
    lowered = text.lower()
    if isinstance(exc, TimeoutError) or any(hint in lowered for hint in _NETWORK_HINTS):
        return (
            f"检索服务连接中断（{action}），已自动重试仍失败。"
            "这通常是网络或 Firecrawl 服务波动，请稍后再试；也可以直接粘贴来源链接/原文。"
        )
    if "401" in text or "403" in text or "unauthorized" in lowered:
        return "Firecrawl 密钥无效或额度不足；请检查 backend/.env 的 FIRECRAWL_API_KEY。"
    return f"Firecrawl {action}失败：{text[:200]}"


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    text = str(exc).lower()
    if "401" in text or "403" in text or "unauthorized" in text:
        return False
    return any(hint in text for hint in _NETWORK_HINTS)


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


def _use_direct_transport(client: object) -> None:
    """绕过会截断 Firecrawl 长连接的系统代理。"""
    import httpx

    http_client = getattr(client, "async_http_client", None)
    inner = getattr(http_client, "_client", None)
    if inner is None:
        return
    # SDK 未暴露 transport 配置，只能在适配层替换底层 httpx client。
    http_client._client = httpx.AsyncClient(
        base_url=inner.base_url,
        headers=dict(inner.headers),
        limits=httpx.Limits(max_keepalive_connections=0),
        trust_env=False,
    )


class FirecrawlSearchProvider:
    name = "firecrawl"

    def __init__(self, settings: Settings) -> None:
        from firecrawl import AsyncFirecrawl

        self._client = AsyncFirecrawl(
            api_key=settings.firecrawl_api_key,
            timeout=settings.search_timeout_seconds,
            max_retries=2,
            backoff_factor=0.5,
        )
        if not settings.firecrawl_trust_env:
            _use_direct_transport(self._client)
        self._timeout = max(10, settings.search_timeout_seconds)

    async def _call(
        self, action: str, factory: Callable[[], Awaitable[_T]]
    ) -> _T:
        last: BaseException | None = None
        for attempt in range(2):
            try:
                return await asyncio.wait_for(factory(), timeout=self._timeout)
            except Exception as exc:  # noqa: BLE001 - 网络异常统一转成可操作提示
                last = exc
                if attempt == 0 and _retryable(exc):
                    await asyncio.sleep(1.5)
                    continue
                break
        assert last is not None
        raise SearchUnavailable(_friendly_error(action, last)) from last

    async def search(self, query: str, *, limit: int = 5) -> list[SearchHit]:
        result = await self._call(
            "搜索",
            lambda: self._client.search(
                query,
                limit=limit,
                sources=["web"],
            ),
        )

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
        document = await self._call(
            "抓取",
            lambda: self._client.scrape(
                url,
                formats=["markdown"],
                only_main_content=True,
            ),
        )

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


_PROVIDER_CACHE: dict[tuple[str, bool, float], SearchProvider] = {}


def get_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "firecrawl" and settings.firecrawl_api_key:
        key = (
            settings.firecrawl_api_key,
            settings.firecrawl_trust_env,
            settings.search_timeout_seconds,
        )
        cached = _PROVIDER_CACHE.get(key)
        if cached is None:
            cached = FirecrawlSearchProvider(settings)
            _PROVIDER_CACHE[key] = cached
        return cached
    return UnavailableSearchProvider()
