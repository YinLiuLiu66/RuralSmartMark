"""模拟时钟控制（decisions #17）：REST 入口，限运营方角色。"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ruralsmartmark.auth import ROLE_OPERATOR, require_role
from ruralsmartmark.sim.engine import engine

router = APIRouter(prefix="/api/sim", tags=["sim"])


class SimControlRequest(BaseModel):
    action: Literal["pause", "resume", "speed", "reset"]
    # action=speed 时必填且 1–10（含）；其余动作忽略
    speed: float | None = None


@router.post("/control", dependencies=[Depends(require_role(ROLE_OPERATOR))])
async def sim_control(req: SimControlRequest) -> dict[str, object]:
    if req.action == "speed" and (req.speed is None or not 1 <= req.speed <= 10):
        raise HTTPException(422, "speed 需在 1–10 之间")
    return {"clock": await engine.control(req.action, req.speed)}
