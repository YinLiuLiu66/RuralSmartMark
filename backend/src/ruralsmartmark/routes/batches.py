from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import SessionDep
from ..models import Batch, ProductProfile
from ..schemas import BatchCreate, BatchOut, BatchWorkspaceOut
from ..services.batch_create import create_batch_for_product
from ..services.workspace import load_workspace

router = APIRouter()


@router.get("/batches", response_model=list[BatchOut])
async def list_batches(
    session: SessionDep, product_id: int | None = None
) -> list[Batch]:
    query = select(Batch).order_by(Batch.id.desc())
    if product_id is not None:
        query = query.where(Batch.product_id == product_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/batches/by-code/{code}", response_model=BatchOut)
async def get_batch_by_code(code: str, session: SessionDep) -> Batch:
    batch = await session.scalar(select(Batch).where(Batch.code == code))
    if batch is None:
        raise HTTPException(status_code=404, detail="batch not found")
    return batch


@router.get("/batches/{batch_id}/workspace", response_model=BatchWorkspaceOut)
async def get_batch_workspace(batch_id: int, session: SessionDep) -> BatchWorkspaceOut:
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
    return await create_batch_for_product(session, product, payload.quantity_kg)
