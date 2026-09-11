"""Unit tests: barcode lookup waterfall priority with a mocked Open Food Facts
client, and the price sanity check. See api/CLAUDE.md → Barcode Lookup Waterfall.
"""

import pytest
from sqlalchemy import delete, select

from app.models.product import Product
from app.models.store_price import StorePrice
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate
from app.services.product_service import ProductService, is_price_sane

# These tests write Product/StorePrice rows directly via the repo, bypassing the
# service's own get-by-barcode-first idempotency — and local Postgres persists
# between test runs (unlike CI's fresh container), so a second local run would hit
# duplicate-barcode violations without cleanup. See progress.md Decisions Log.
_TEST_BARCODES = ["8901058851639", "1111111111111", "2222222222222"]


@pytest.fixture(autouse=True)
async def _cleanup_test_products(db_session):
    yield
    for barcode in _TEST_BARCODES:
        product = (await db_session.execute(select(Product).where(Product.barcode == barcode))).scalar_one_or_none()
        if product is not None:
            await db_session.execute(delete(StorePrice).where(StorePrice.product_id == product.id))
            await db_session.delete(product)
    await db_session.commit()


class FakeOpenFoodFactsClient:
    def __init__(self, result: dict | None = None) -> None:
        self.result = result
        self.calls = 0

    async def lookup(self, barcode: str) -> dict | None:
        self.calls += 1
        return self.result


@pytest.fixture
def product_repo(db_session):
    return ProductRepository(db_session)


def test_is_price_sane_rejects_zero_and_negative():
    assert is_price_sane(0, None) is False
    assert is_price_sane(-100, None) is False


def test_is_price_sane_rejects_above_ceiling():
    assert is_price_sane(5_000_001, None) is False


def test_is_price_sane_accepts_ceiling_boundary():
    assert is_price_sane(5_000_000, None) is True


def test_is_price_sane_rejects_more_than_3x_existing():
    assert is_price_sane(301, 100) is False
    assert is_price_sane(300, 100) is True


async def test_lookup_falls_back_to_open_food_facts_when_no_local_product(product_repo):
    off_client = FakeOpenFoodFactsClient({"name": "Parle-G", "brand": "Parle", "category": "Biscuits"})
    service = ProductService(product_repo, off_client)

    result = await service.lookup_product("8901058851639", store_id=None)

    assert result is not None
    assert result.name == "Parle-G"
    assert result.price_paise is None
    assert result.source is None
    assert off_client.calls == 1


async def test_lookup_returns_none_when_not_found_anywhere(product_repo):
    off_client = FakeOpenFoodFactsClient(None)
    service = ProductService(product_repo, off_client)

    result = await service.lookup_product("0000000000000", store_id=None)

    assert result is None


async def test_lookup_uses_confident_local_price_without_calling_open_food_facts(product_repo):
    off_client = FakeOpenFoodFactsClient({"name": "Should not be used"})
    service = ProductService(product_repo, off_client)

    product = await product_repo.create_product("1111111111111", "Amul Milk", None, None)
    await product_repo.upsert_price(product.id, None, 5000, source="receipt_ocr", confidence=0.95)

    result = await service.lookup_product("1111111111111", store_id=None)

    assert result is not None
    assert result.name == "Amul Milk"
    assert result.price_paise == 5000
    assert off_client.calls == 0


async def test_lookup_keeps_low_confidence_local_price_when_off_has_no_price_data(product_repo):
    off_client = FakeOpenFoodFactsClient({"name": "OFF Name", "brand": "OFF Brand"})
    service = ProductService(product_repo, off_client)

    await service.create_manual_product(ProductCreate(barcode="2222222222222", name="Tata Salt", price_paise=2500))

    # Manual entries sit exactly at the waterfall's ">0.20" boundary, so Open Food
    # Facts is still queried — but since it has no price data, the existing manual
    # price and product identity are kept rather than discarded.
    result = await service.lookup_product("2222222222222", store_id=None)

    assert result is not None
    assert result.name == "Tata Salt"
    assert result.price_paise == 2500
    assert off_client.calls == 1
