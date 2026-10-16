"""测试夹具：指向独立测试库并在每轮会话建表/种演示账号。

测试库 <dbname>_test 由本模块按需创建，避免污染开发库。
"""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from ruralsmartmark.config import settings
from ruralsmartmark.models import Base

TEST_DB = settings.database_url + "_test"


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_db() -> None:
    async def setup() -> None:
        # 连到默认库建测试库（PG 不能在事务里 CREATE DATABASE）
        admin_engine = create_async_engine(
            settings.database_url, isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname='ruralsmartmark_test'")
            )
            if not exists:
                await conn.execute(text("CREATE DATABASE ruralsmartmark_test"))
        await admin_engine.dispose()

        engine = create_async_engine(TEST_DB, isolation_level="AUTOCOMMIT")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(setup())

    # 种演示账号
    from ruralsmartmark.auth import hash_password
    from ruralsmartmark.models import User
    from ruralsmartmark.seed import DEMO_ACCOUNTS

    async def seed() -> None:
        engine = create_async_engine(TEST_DB)
        async with engine.begin() as conn:
            for username, password, role in DEMO_ACCOUNTS:
                await conn.execute(
                    User.__table__.insert().values(
                        username=username,
                        password_hash=hash_password(password),
                        role=role,
                    )
                )
        await engine.dispose()

    asyncio.run(seed())

    yield


@pytest.fixture(autouse=True)
def _use_test_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """每个测试把全局 engine/session_factory 换成测试库的新实例。

    必须每测试新建 engine 且禁池化：asyncpg 连接绑定创建时的事件循环，
    TestClient 每个请求跑在独立循环里，连接池复用旧连接会报
    attached to a different loop；NullPool 让每次取用都新建连接。
    """
    from sqlalchemy import pool as sa_pool
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from ruralsmartmark import db as db_module

    engine = create_async_engine(TEST_DB, poolclass=sa_pool.NullPool)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(
        db_module,
        "session_factory",
        async_sessionmaker(engine, expire_on_commit=False),
    )
    yield
