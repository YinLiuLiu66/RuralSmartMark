import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import get_settings
from ..db import build_engine, init_db
from . import seed_demo


async def main() -> None:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    await init_db(engine)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        counts = await seed_demo(session, artifact_dir=settings.artifact_path)
    await engine.dispose()
    print(f"seeded: {counts}")


if __name__ == "__main__":
    asyncio.run(main())
