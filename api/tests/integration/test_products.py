"""Integration tests: barcode lookup and manual product creation via httpx AsyncClient.
See api/CLAUDE.md → Test Structure.
"""

import pytest
from sqlalchemy import delete, select

from app.models.product import Product
from app.models.store_price import StorePrice
from app.routers import products as products_router

# Local Postgres persists between test runs (unlike CI's fresh container per run), so
# products created here would hit duplicate-barcode/leftover-price issues on rerun.
_TEST_BARCODES = ["3333333333333", "4444444444444", "5555555555555"]


@pytest.fixture(autouse=True)
def _stub_open_food_facts(monkeypatch):
    """Integration tests must never hit the real Open Food Facts API."""

    class _StubClient:
        async def lookup(self, barcode: str) -> dict | None:
            return None

    monkeypatch.setattr(products_router, "OpenFoodFactsClient", _StubClient)


@pytest.fixture(autouse=True)
async def _cleanup_test_products(db_session):
    yield
    for barcode in _TEST_BARCODES:
        product = (await db_session.execute(select(Product).where(Product.barcode == barcode))).scalar_one_or_none()
        if product is not None:
            await db_session.execute(delete(StorePrice).where(StorePrice.product_id == product.id))
            await db_session.delete(product)
    await db_session.commit()


async def test_create_manual_product_then_look_it_up(client):
    create_response = await client.post(
        "/v1/products", json={"barcode": "3333333333333", "name": "Tata Salt", "price_paise": 2500}
    )
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["name"] == "Tata Salt"
    assert body["price_paise"] == 2500
    assert body["confidence_score"] == 0.20
    assert body["source"] == "manual"

    lookup_response = await client.get("/v1/products/3333333333333")
    assert lookup_response.status_code == 200
    assert lookup_response.json()["price_paise"] == 2500


async def test_create_manual_product_without_price(client):
    response = await client.post("/v1/products", json={"barcode": "4444444444444", "name": "Unpriced Item"})
    assert response.status_code == 201
    body = response.json()
    assert body["price_paise"] is None
    assert body["confidence_score"] == 0.0
    assert body["source"] is None


async def test_create_manual_product_rejects_insane_price(client):
    response = await client.post(
        "/v1/products", json={"barcode": "5555555555555", "name": "Suspicious Item", "price_paise": 6_000_000}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PRICE_REJECTED"


async def test_get_unknown_product_returns_404(client):
    response = await client.get("/v1/products/9999999999999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"
