from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routes import artifacts, batches, demo, health, knowledge, pipeline, products, trace


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="乡土印记 v2", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(products.router, prefix="/api", tags=["products"])
    app.include_router(knowledge.router, prefix="/api", tags=["knowledge"])
    app.include_router(batches.router, prefix="/api", tags=["batches"])
    app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])
    app.include_router(artifacts.router, prefix="/api", tags=["artifacts"])
    app.include_router(demo.router, prefix="/api", tags=["demo"])
    app.include_router(trace.router, prefix="/api", tags=["trace"])
    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    target = "ruralsmartmark.main:app" if settings.debug else app
    uvicorn.run(
        target,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
