from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..deps import SessionDep
from ..models import ProductProfile
from ..schemas import KnowledgeDocOut
from ..services.knowledge import list_knowledge_docs

router = APIRouter()


@router.get("/knowledge", response_model=list[KnowledgeDocOut])
async def list_product_knowledge(
    session: SessionDep, product_slug: str = "zhaotong-ugly-apple"
) -> list[KnowledgeDocOut]:
    product = await session.scalar(
        select(ProductProfile).where(ProductProfile.slug == product_slug)
    )
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    docs = await list_knowledge_docs(session, product.id)
    return [KnowledgeDocOut.model_validate(doc) for doc in docs]
