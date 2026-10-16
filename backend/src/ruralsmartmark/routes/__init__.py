"""API 路由模块。"""

from ruralsmartmark.routes.auth import router as auth_router
from ruralsmartmark.routes.sim import router as sim_router
from ruralsmartmark.routes.world import router as world_router

__all__ = ["auth_router", "sim_router", "world_router"]
