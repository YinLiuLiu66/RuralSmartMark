from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


def build_engine(url: str) -> AsyncEngine:
    engine = create_async_engine(url, echo=False, future=True)
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


settings = get_settings()
engine = build_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db(target: AsyncEngine | None = None) -> None:
    from . import models  # noqa: F401

    engine_to_use = target or engine
    async with engine_to_use.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
