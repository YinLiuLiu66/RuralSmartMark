from fastapi import APIRouter

from ..agents.runtime import RuntimeDep
from ..deps import SessionDep
from ..schemas import DemoResetOut
from ..seed import seed_demo

router = APIRouter()


@router.post("/demo/reset", response_model=DemoResetOut)
async def reset_demo(session: SessionDep, runtime: RuntimeDep) -> DemoResetOut:
    counts = await seed_demo(
        session,
        reset=True,
        public_base_url=runtime.settings.public_base_url,
        artifact_dir=runtime.artifact_dir,
    )
    return DemoResetOut(**counts)
