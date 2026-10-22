import pytest

from ruralsmartmark.providers.search import FirecrawlSearchProvider, SearchUnavailable


class _FlakyClient:
    def __init__(self, message: str) -> None:
        self.message = message
        self.calls = 0

    async def search(self, *_args, **_kwargs):
        self.calls += 1
        raise RuntimeError(self.message)

    async def scrape(self, *_args, **_kwargs):
        self.calls += 1
        raise RuntimeError(self.message)


def _provider(client: _FlakyClient) -> FirecrawlSearchProvider:
    provider = FirecrawlSearchProvider.__new__(FirecrawlSearchProvider)
    provider._client = client  # type: ignore[attr-defined]
    provider._timeout = 5  # type: ignore[attr-defined]
    return provider


async def test_search_retries_network_error(monkeypatch):
    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("ruralsmartmark.providers.search.asyncio.sleep", no_sleep)
    client = _FlakyClient("SSL: UNEXPECTED_EOF_WHILE_READING")
    provider = _provider(client)

    with pytest.raises(SearchUnavailable) as error:
        await provider.search("平泉香菇")

    assert client.calls == 2
    assert "连接中断" in str(error.value)
    assert "SSL" not in str(error.value)


async def test_search_does_not_retry_invalid_key(monkeypatch):
    async def no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("ruralsmartmark.providers.search.asyncio.sleep", no_sleep)
    client = _FlakyClient("401 Unauthorized")
    provider = _provider(client)

    with pytest.raises(SearchUnavailable) as error:
        await provider.search("平泉香菇")

    assert client.calls == 1
    assert "密钥无效" in str(error.value)
