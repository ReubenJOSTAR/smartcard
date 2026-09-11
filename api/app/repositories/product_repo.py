"""Product / StorePrice DB queries. See api/CLAUDE.md → Barcode Lookup Waterfall.

`upsert_price` targets one of two partial unique indexes depending on whether
store_id is known — see app/models/store_price.py for why a single composite
UniqueConstraint doesn't work when store_id is NULL.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.store_price import StorePrice


class ProductRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_barcode(self, barcode: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.barcode == barcode))
        return result.scalar_one_or_none()

    async def get_price(self, product_id: uuid.UUID, store_id: uuid.UUID | None) -> StorePrice | None:
        stmt = select(StorePrice).where(StorePrice.product_id == product_id, StorePrice.store_id == store_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_product(self, barcode: str, name: str, brand: str | None, category: str | None) -> Product:
        product = Product(barcode=barcode, name=name, brand=brand, category=category)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def upsert_price(
        self,
        product_id: uuid.UUID,
        store_id: uuid.UUID | None,
        price_paise: int,
        source: str,
        confidence: float,
    ) -> StorePrice:
        if store_id is None:
            index_elements = ["product_id"]
            index_where = StorePrice.store_id.is_(None)
        else:
            index_elements = ["product_id", "store_id"]
            index_where = StorePrice.store_id.is_not(None)

        stmt = (
            insert(StorePrice)
            .values(
                product_id=product_id,
                store_id=store_id,
                price_paise=price_paise,
                source=source,
                confidence_score=confidence,
            )
            .on_conflict_do_update(
                index_elements=index_elements,
                index_where=index_where,
                set_={
                    "price_paise": price_paise,
                    "source": source,
                    "confidence_score": confidence,
                    "last_seen": func.now(),
                },
            )
            .returning(StorePrice)
            # The (product_id, store_id) pair may already be loaded in this session's
            # identity map from an earlier get_price() call — without this, SQLAlchemy
            # returns that stale cached object instead of the just-updated row.
            .execution_options(populate_existing=True)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()
