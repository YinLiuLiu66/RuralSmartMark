from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import SessionDep
from ..models import Batch, ProductProfile
from ..schemas import BatchCreate, BatchOut, BatchWorkspaceOut
from ..services.workspace import load_workspace

router = APIRouter()


async def _next_code(session: AsyncSession) -> str:
    year = datetime.now().year
    prefix = f"ZT-{year}-"
    count = await session.scalar(
        select(func.count()).select_from(Batch).where(Batch.code.like(f"{prefix}%"))
    )
    return f"{prefix}{int(count or 0) + 1:03d}"


@router.get("/batches", response_model=list[BatchOut])
async def list_batches(session: SessionDep) -> list[Batch]:
    result = await session.execute(select(Batch).order_by(Batch.id.desc()))
    return list(result.scalars().all())


@router.get("/batches/by-code/{code}", response_model=BatchOut)
async def get_batch_by_code(code: str, session: SessionDep) -> Batch:
    batch = await session.scalar(select(Batch).where(Batch.code == code))
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return batch


@router.get("/batches/{batch_id}/workspace", response_model=BatchWorkspaceOut)
async def get_batch_workspace(
    batch_id: int, session: SessionDep
) -> BatchWorkspaceOut:
    workspace = await load_workspace(session, batch_id)
    if workspace is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return workspace


@router.get("/batches/{batch_id}", response_model=BatchOut)
async def get_batch(batch_id: int, session: SessionDep) -> Batch:
    batch = await session.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return batch


@router.post("/batches", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
async def create_batch(payload: BatchCreate, session: SessionDep) -> Batch:
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == payload.product_slug)
    )
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")

    batch = Batch(
        product_id=product.id,
        code=await _next_code(session),
        quantity_kg=payload.quantity_kg,
        state="raw",
        current_station="intake",
    )
    session.add(batch)
    await session.commit()
    await session.refresh(batch)
    return batch
