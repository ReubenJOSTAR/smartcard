"""Shopping session business logic — create/fetch, item CRUD, finish, history.
See api/CLAUDE.md → Service Layer and root CLAUDE.md §6 domain invariants.
"""

import uuid

from fastapi import HTTPException

from app.models.shopping_session import ShoppingSession
from app.repositories.session_repo import SessionRepository
from app.schemas.history import HistoryResponse, HistorySessionSummary
from app.schemas.session import SessionItemResponse, SessionResponse
from app.services.product_service import ProductService


def _session_not_found() -> HTTPException:
    return HTTPException(
        status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": "Session not found", "details": {}}
    )


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=403, detail={"code": "FORBIDDEN", "message": "This isn't your session", "details": {}}
    )


def _already_finished() -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "code": "SESSION_ALREADY_FINISHED",
            "message": "This session is complete — start a new one",
            "details": {},
        },
    )


class SessionService:
    def __init__(self, session_repo: SessionRepository, product_service: ProductService) -> None:
        self.session_repo = session_repo
        self.product_service = product_service

    async def create_session(self, user_id: uuid.UUID, store_name_text: str, budget_paise: int) -> SessionResponse:
        # Domain invariant (root CLAUDE.md §6): exactly one active session per user.
        existing = await self.session_repo.get_active_for_user(user_id)
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "SESSION_ALREADY_ACTIVE",
                    "message": "You already have an active shopping session",
                    "details": {},
                },
            )
        session = await self.session_repo.create(user_id, store_name_text, budget_paise)
        return await self._to_response(session)

    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionResponse:
        session = await self._get_owned_session(session_id, user_id)
        return await self._to_response(session)

    async def add_item(
        self, session_id: uuid.UUID, user_id: uuid.UUID, barcode: str, quantity: int
    ) -> SessionResponse:
        session = await self._get_owned_session(session_id, user_id)
        self._require_active(session)

        found = await self.product_service.find_product_and_price(barcode, session.store_id)
        if found is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "PRODUCT_NOT_FOUND", "message": "We don't recognise this product yet", "details": {}},
            )
        product, price = found
        price_paise = price.price_paise if price is not None else 0

        await self.session_repo.add_item(session_id, product.id, quantity, price_paise)
        return await self._to_response(session)

    async def update_item_quantity(
        self, session_id: uuid.UUID, user_id: uuid.UUID, item_id: uuid.UUID, quantity: int
    ) -> SessionResponse:
        session = await self._get_owned_session(session_id, user_id)
        self._require_active(session)

        item = await self.session_repo.get_item(session_id, item_id)
        if item is None:
            raise _session_not_found()
        await self.session_repo.update_item_quantity(item, quantity)
        return await self._to_response(session)

    async def remove_item(self, session_id: uuid.UUID, user_id: uuid.UUID, item_id: uuid.UUID) -> SessionResponse:
        session = await self._get_owned_session(session_id, user_id)
        self._require_active(session)

        item = await self.session_repo.get_item(session_id, item_id)
        if item is None:
            raise _session_not_found()
        await self.session_repo.delete_item(item)
        return await self._to_response(session)

    async def finish_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionResponse:
        session = await self._get_owned_session(session_id, user_id)
        self._require_active(session)

        session = await self.session_repo.update_status(session, "finished")
        return await self._to_response(session)

    async def list_history(self, user_id: uuid.UUID, limit: int, offset: int) -> HistoryResponse:
        sessions, total = await self.session_repo.list_for_user(user_id, limit, offset)
        summaries = []
        for session in sessions:
            items = await self.session_repo.list_items_with_product(session.id)
            estimated_total_paise = sum(item.estimated_price_paise * item.quantity for item, _ in items)
            summaries.append(
                HistorySessionSummary(
                    id=session.id,
                    store_name_text=session.store_name_text,
                    budget_paise=session.budget_paise,
                    status=session.status,
                    item_count=len(items),
                    estimated_total_paise=estimated_total_paise,
                    created_at=session.created_at,
                )
            )
        return HistoryResponse(sessions=summaries, total=total, limit=limit, offset=offset)

    async def _get_owned_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ShoppingSession:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise _session_not_found()
        if session.user_id != user_id:
            raise _forbidden()
        return session

    @staticmethod
    def _require_active(session: ShoppingSession) -> None:
        if session.status != "active":
            raise _already_finished()

    async def _to_response(self, session: ShoppingSession) -> SessionResponse:
        rows = await self.session_repo.list_items_with_product(session.id)
        items = [
            SessionItemResponse(
                id=item.id,
                product_id=item.product_id,
                barcode=product.barcode,
                name=product.name,
                quantity=item.quantity,
                estimated_price_paise=item.estimated_price_paise,
                line_total_paise=item.estimated_price_paise * item.quantity,
            )
            for item, product in rows
        ]
        estimated_total_paise = sum(item.line_total_paise for item in items)
        return SessionResponse(
            id=session.id,
            store_id=session.store_id,
            store_name_text=session.store_name_text,
            budget_paise=session.budget_paise,
            status=session.status,
            items=items,
            estimated_total_paise=estimated_total_paise,
            created_at=session.created_at,
        )
