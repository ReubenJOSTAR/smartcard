"""ShoppingSession / SessionItem DB queries. See api/CLAUDE.md → Service Layer example."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.session_item import SessionItem
from app.models.shopping_session import ShoppingSession


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_for_user(self, user_id: uuid.UUID) -> ShoppingSession | None:
        stmt = select(ShoppingSession).where(
            ShoppingSession.user_id == user_id, ShoppingSession.status == "active"
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID, store_name_text: str, budget_paise: int) -> ShoppingSession:
        session = ShoppingSession(
            user_id=user_id, store_name_text=store_name_text, budget_paise=budget_paise, status="active"
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> ShoppingSession | None:
        return await self.db.get(ShoppingSession, session_id)

    async def update_status(self, session: ShoppingSession, status: str) -> ShoppingSession:
        session.status = status
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_item(
        self, session_id: uuid.UUID, product_id: uuid.UUID, quantity: int, price_paise: int
    ) -> SessionItem:
        item = SessionItem(
            session_id=session_id, product_id=product_id, quantity=quantity, estimated_price_paise=price_paise
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_item(self, session_id: uuid.UUID, item_id: uuid.UUID) -> SessionItem | None:
        stmt = select(SessionItem).where(SessionItem.id == item_id, SessionItem.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_item_quantity(self, item: SessionItem, quantity: int) -> SessionItem:
        item.quantity = quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_item(self, item: SessionItem) -> None:
        await self.db.delete(item)
        await self.db.commit()

    async def list_items_with_product(self, session_id: uuid.UUID) -> list[tuple[SessionItem, Product]]:
        stmt = (
            select(SessionItem, Product)
            .join(Product, SessionItem.product_id == Product.id)
            .where(SessionItem.session_id == session_id)
            .order_by(SessionItem.created_at)
        )
        result = await self.db.execute(stmt)
        return [(item, product) for item, product in result.all()]

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[ShoppingSession], int]:
        total = (
            await self.db.execute(
                select(func.count()).select_from(ShoppingSession).where(ShoppingSession.user_id == user_id)
            )
        ).scalar_one()
        stmt = (
            select(ShoppingSession)
            .where(ShoppingSession.user_id == user_id)
            .order_by(ShoppingSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total
