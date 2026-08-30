"""Store DB queries — placeholder. See api/CLAUDE.md → GET /v1/stores/nearby (stubbed 501 in MVP)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import Store


class StoreRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, store_id: int) -> Store | None:
        ...
