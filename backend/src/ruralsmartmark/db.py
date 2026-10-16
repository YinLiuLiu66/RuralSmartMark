"""Async engine + sessionmaker（全局单例）。

演示项目用模块级单例足够；连接串来自 Settings.database_url。
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ruralsmartmark.config import settings

engine: AsyncEngine = create_async_engine(settings.database_url, echo=False)

session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖：每请求一个会话。"""
    async with session_factory() as session:
        yield session
