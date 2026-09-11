"""User DB queries."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(select(User).where(User.phone_number == phone))
        return result.scalar_one_or_none()

    async def create(self, phone: str) -> User:
        user = User(phone_number=phone)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
