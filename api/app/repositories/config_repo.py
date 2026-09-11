"""Config table queries — single row, id=1. See api/CLAUDE.md → Database Rules."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config import Config


class ConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self) -> Config | None:
        return await self.db.get(Config, 1)
