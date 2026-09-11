"""Session routes — create, fetch, item CRUD, finish. See api/CLAUDE.md → Service Layer example."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.repositories.product_repo import ProductRepository
from app.repositories.session_repo import SessionRepository
from app.schemas.session import SessionCreate, SessionItemCreate, SessionItemUpdate, SessionResponse
from app.services.open_food_facts import OpenFoodFactsClient
from app.services.product_service import ProductService
from app.services.session_service import SessionService

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


def _service(db: AsyncSession = Depends(get_db)) -> SessionService:
    product_service = ProductService(ProductRepository(db), OpenFoodFactsClient())
    return SessionService(SessionRepository(db), product_service)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    user_id: str = Depends(get_current_user_id),
    service: SessionService = Depends(_service),
) -> SessionResponse:
    return await service.create_session(uuid.UUID(user_id), body.store_name_text, body.budget_paise)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: SessionService = Depends(_service),
) -> SessionResponse:
    return await service.get_session(session_id, uuid.UUID(user_id))


@router.post("/{session_id}/items", response_model=SessionResponse, status_code=201)
async def add_item(
    session_id: uuid.UUID,
    body: SessionItemCreate,
    user_id: str = Depends(get_current_user_id),
    service: SessionService = Depends(_service),
) -> SessionResponse:
    return await service.add_item(session_id, uuid.UUID(user_id), body.barcode, body.quantity)


@router.patch("/{session_id}/items/{item_id}", response_model=SessionResponse)
async def update_item(
    session_id: uuid.UUID,
    item_id: uuid.UUID,
    body: SessionItemUpdate,
    user_id: str = Depends(get_current_user_id),
    service: SessionService = Depends(_service),
) -> SessionResponse:
    return await service.update_item_quantity(session_id, uuid.UUID(user_id), item_id, body.quantity)


@router.delete("/{session_id}/items/{item_id}", response_model=SessionResponse)
async def delete_item(
    session_id: uuid.UUID,
    item_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: SessionService = Depends(_service),
) -> SessionResponse:
    return await service.remove_item(session_id, uuid.UUID(user_id), item_id)


@router.post("/{session_id}/finish", response_model=SessionResponse)
async def finish_session(
    session_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    service: SessionService = Depends(_service),
) -> SessionResponse:
    return await service.finish_session(session_id, uuid.UUID(user_id))
