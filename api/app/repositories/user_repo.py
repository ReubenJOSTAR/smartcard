"""User DB queries — placeholder. See progress.md → Backend — Auth."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_phone(self, phone: str) -> User | None:
        ...

    async def create(self, phone: str) -> User:
        ...
