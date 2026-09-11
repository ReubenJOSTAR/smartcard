"""Barcode lookup waterfall (DB → Open Food Facts → manual) and price sanity checks.
See api/CLAUDE.md → Barcode Lookup Waterfall.
"""

import uuid

from fastapi import HTTPException

from app.models.product import Product
from app.models.store_price import StorePrice
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse
from app.services.open_food_facts import OpenFoodFactsClient

MIN_USABLE_CONFIDENCE = 0.20
MANUAL_NO_RECEIPT_CONFIDENCE = 0.20

MAX_PRICE_PAISE = 5_000_000  # > ₹50,000 is rejected as an obvious error
MAX_PRICE_MULTIPLE_OF_EXISTING = 3


def is_price_sane(price_paise: int, existing_price_paise: int | None) -> bool:
    if price_paise <= 0 or price_paise > MAX_PRICE_PAISE:
        return False
    if existing_price_paise and price_paise > existing_price_paise * MAX_PRICE_MULTIPLE_OF_EXISTING:
        return False
    return True


class ProductService:
    def __init__(self, product_repo: ProductRepository, off_client: OpenFoodFactsClient) -> None:
        self.product_repo = product_repo
        self.off_client = off_client

    async def lookup_product(self, barcode: str, store_id: uuid.UUID | None) -> ProductResponse | None:
        found = await self.find_product_and_price(barcode, store_id)
        if found is None:
            return None
        product, price = found
        return self._to_response(product, price)

    async def find_product_and_price(
        self, barcode: str, store_id: uuid.UUID | None
    ) -> tuple[Product, StorePrice | None] | None:
        """DB → Open Food Facts waterfall, returning the raw ORM rows (with `Product.id`)
        rather than a response schema — used by callers (e.g. session item add) that need
        the product's id, not just its display fields.
        """
        product = await self.product_repo.get_by_barcode(barcode)
        price = None
        if product is not None:
            price = await self.product_repo.get_price(product.id, store_id)
            if price is not None and price.confidence_score > MIN_USABLE_CONFIDENCE:
                return product, price

        # Either no product yet, or one with a low-confidence/no price — ask Open
        # Food Facts too. It has no price data, so it can only fill in product
        # identity, not replace a price we already know about (even a rough one).
        off_result = await self.off_client.lookup(barcode)
        if off_result is not None and product is None:
            product = await self.product_repo.create_product(
                barcode, off_result["name"], off_result.get("brand"), off_result.get("category")
            )

        if product is not None:
            return product, price

        return None

    async def create_manual_product(self, data: ProductCreate) -> ProductResponse:
        product = await self.product_repo.get_by_barcode(data.barcode)
        if product is None:
            product = await self.product_repo.create_product(data.barcode, data.name, data.brand, data.category)

        price = None
        if data.price_paise is not None:
            existing_price = await self.product_repo.get_price(product.id, data.store_id)
            existing_price_paise = existing_price.price_paise if existing_price is not None else None
            if not is_price_sane(data.price_paise, existing_price_paise):
                raise HTTPException(
                    status_code=422,
                    detail={"code": "PRICE_REJECTED", "message": "This price looks incorrect", "details": {}},
                )
            price = await self.product_repo.upsert_price(
                product.id,
                data.store_id,
                data.price_paise,
                source="manual",
                confidence=MANUAL_NO_RECEIPT_CONFIDENCE,
            )

        return self._to_response(product, price)

    @staticmethod
    def _to_response(product: Product, price: StorePrice | None) -> ProductResponse:
        return ProductResponse(
            barcode=product.barcode,
            name=product.name,
            brand=product.brand,
            category=product.category,
            price_paise=price.price_paise if price is not None else None,
            confidence_score=price.confidence_score if price is not None else 0.0,
            source=price.source if price is not None else None,
        )
