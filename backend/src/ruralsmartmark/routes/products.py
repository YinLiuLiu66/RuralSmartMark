from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..deps import SessionDep
from ..models import ProductProfile
from ..schemas import ProductOut

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
async def list_products(session: SessionDep) -> list[ProductProfile]:
    result = await session.execute(
        select(ProductProfile)
        .where(ProductProfile.is_active.is_(True))
        .order_by(ProductProfile.id)
    )
    return list(result.scalars().all())


@router.get("/products/{slug}", response_model=ProductOut)
async def get_product(slug: str, session: SessionDep) -> ProductProfile:
    product = await session.scalar(select(ProductProfile).where(ProductProfile.slug == slug))
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return product
