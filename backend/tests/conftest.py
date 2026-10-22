import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

import ruralsmartmark.models  # noqa: F401 - register all tables on Base.metadata
from ruralsmartmark.agents.runtime import AgentRuntime, get_runtime
from ruralsmartmark.config import get_settings
from ruralsmartmark.db import Base, build_engine, get_session
from ruralsmartmark.main import app
from ruralsmartmark.providers.llm import MockLLMProvider, get_llm_provider


@pytest_asyncio.fixture
async def engine(tmp_path):
    db_path = tmp_path / "test.db"
    test_engine = build_engine(f"sqlite+aiosqlite:///{db_path}")
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session


@pytest_asyncio.fixture
async def client(engine, tmp_path):
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_session():
        async with maker() as db_session:
            yield db_session

    settings = get_settings()
    llm = get_llm_provider(settings) if os.getenv("RSM_REAL_LLM") == "1" else MockLLMProvider()
    runtime = AgentRuntime(
        settings=settings,
        llm=llm,
        artifact_dir=tmp_path / "artifacts",
        allow_mock_fallback=True,
    )
    runtime.artifact_dir.mkdir(parents=True, exist_ok=True)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_runtime] = lambda: runtime
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
