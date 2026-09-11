"""Product routes — barcode lookup + manual creation.
See api/CLAUDE.md → Barcode Lookup Waterfall and root CLAUDE.md → Product Not Found flow.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse
from app.services.open_food_facts import OpenFoodFactsClient
from app.services.product_service import ProductService

router = APIRouter(prefix="/v1/products", tags=["products"])


@router.get("/{barcode}", response_model=ProductResponse)
async def get_product(
    barcode: str,
    store_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    service = ProductService(ProductRepository(db), OpenFoodFactsClient())
    result = await service.lookup_product(barcode, store_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRODUCT_NOT_FOUND", "message": "We don't recognise this product yet", "details": {}},
        )
    return result


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db)) -> ProductResponse:
    service = ProductService(ProductRepository(db), OpenFoodFactsClient())
    return await service.create_manual_product(body)
