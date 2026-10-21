"""API 路由模块。"""

from ruralsmartmark.routes.agents import router as agents_router
from ruralsmartmark.routes.auth import router as auth_router
from ruralsmartmark.routes.sim import router as sim_router
from ruralsmartmark.routes.trace import router as trace_router
from ruralsmartmark.routes.world import router as world_router

__all__ = [
    "agents_router",
    "auth_router",
    "sim_router",
    "trace_router",
    "world_router",
]
