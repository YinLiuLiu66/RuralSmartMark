from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ruralsmartmark.auth import (
    ROLE_OPERATOR,
    User,
    get_current_user,
    require_role,
)
from ruralsmartmark.config import settings
from ruralsmartmark.routes import auth_router

app = FastAPI(
    title="RuralSmartMark API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# M2 会把 sim 路由拆成独立模块；M1 先挂假路由验权（05 清单 M1-c 测试要求）
sim_router = APIRouter(prefix="/api/sim", tags=["sim"])


@sim_router.post("/control", dependencies=[Depends(require_role(ROLE_OPERATOR))])
async def sim_control() -> dict[str, str]:
    """占位：M2 实现时钟控制；M1 仅验证 operator 角色门槛。"""
    return {"detail": "not implemented until M2"}


app.include_router(sim_router)


@app.get("/api/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ruralsmartmark"}


@app.get("/api/auth/me", tags=["auth"])
async def who_am_i(
    user: User = Depends(get_current_user),  # noqa: B008 — FastAPI 依赖注入惯用法
) -> dict[str, str]:
    """M1 验收探针：带合法 token 返回身份，否则 401。"""
    return {"username": user.username, "role": user.role}
