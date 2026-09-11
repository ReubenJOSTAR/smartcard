"""History route — paginated past sessions. See api/CLAUDE.md → GET /v1/history."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.product_repo import ProductRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.history import HistoryResponse
from app.services.open_food_facts import OpenFoodFactsClient
from app.services.product_service import ProductService
from app.services.session_service import SessionService

router = APIRouter(prefix="/v1/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
async def get_history(
    limit: int = Query(default=20, gt=0, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    product_service = ProductService(ProductRepository(db), OpenFoodFactsClient())
    service = SessionService(SessionRepository(db), product_service)
    return await service.list_history(uuid.UUID(user_id), limit, offset)
