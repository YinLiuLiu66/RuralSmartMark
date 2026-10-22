import os

import pytest

from ruralsmartmark.config import get_settings
from ruralsmartmark.providers.search import FirecrawlSearchProvider

settings = get_settings()

pytestmark = [
    pytest.mark.skipif(
        os.getenv("RSM_REAL_SEARCH") != "1",
        reason="真实 Firecrawl 搜索会消耗 credits；显式设置 RSM_REAL_SEARCH=1 才跑",
    ),
    pytest.mark.skipif(
        not settings.firecrawl_api_key,
        reason="没有配置 FIRECRAWL_API_KEY",
    ),
]


async def test_firecrawl_search_and_scrape():
    provider = FirecrawlSearchProvider(settings)
    hits = await provider.search("昭通苹果 地理标志 公告", limit=2)
    assert hits
    page = await provider.scrape(hits[0].url)
    assert len(page.markdown) > 100
