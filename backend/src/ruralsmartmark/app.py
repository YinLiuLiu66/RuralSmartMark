from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ruralsmartmark.auth import User, get_current_user
from ruralsmartmark.config import settings
from ruralsmartmark.routes import (
    agents_router,
    auth_router,
    sim_router,
    trace_router,
    world_router,
)
from ruralsmartmark.sim.engine import engine as sim_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 后端重启 = 演示起点：重建剧本世界，拉起 tick 主循环（单 worker 运行）
    await sim_engine.start()
    yield
    await sim_engine.stop()


app = FastAPI(
    title="RuralSmartMark API",
    version="0.2.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sim_router)
app.include_router(world_router)
app.include_router(agents_router)
app.include_router(trace_router)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ruralsmartmark"}


@app.get("/api/auth/me", tags=["auth"])
async def who_am_i(
    user: User = Depends(get_current_user),  # noqa: B008 — FastAPI 依赖注入惯用法
) -> dict[str, str]:
    """M1 验收探针：带合法 token 返回身份，否则 401。"""
    return {"username": user.username, "role": user.role}
