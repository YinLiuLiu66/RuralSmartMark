from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ..deps import SessionDep
from ..schemas import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health(session: SessionDep) -> HealthOut:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return HealthOut(status="ok", app="ruralsmartmark-v2", db="ok")
