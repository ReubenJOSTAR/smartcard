"""Product / StorePrice DB queries — placeholder. See progress.md → Backend — Products."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_barcode_and_store(self, barcode: str, store_id: int | None) -> Product | None:
        ...

    async def upsert_price(self, barcode: str, store_id: int | None, price_paise: int, confidence: float) -> None:
        ...
