from fastapi import APIRouter

from ..deps import SessionDep
from ..schemas import DemoResetOut
from ..seed import seed_demo

router = APIRouter()


@router.post("/demo/reset", response_model=DemoResetOut)
async def reset_demo(session: SessionDep) -> DemoResetOut:
    counts = await seed_demo(session, reset=True)
    return DemoResetOut(**counts)
