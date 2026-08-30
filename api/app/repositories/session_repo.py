"""ShoppingSession / SessionItem DB queries — placeholder. See progress.md → Backend — Sessions."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopping_session import ShoppingSession


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_active_for_user(self, user_id: str) -> ShoppingSession | None:
        ...

    async def create(self, user_id: str, store_name_text: str, budget_paise: int) -> ShoppingSession:
        ...

    async def get_by_id(self, session_id: str) -> ShoppingSession | None:
        ...
