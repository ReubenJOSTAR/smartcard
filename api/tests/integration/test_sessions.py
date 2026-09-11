"""Integration tests: session create/fetch, item CRUD, finish, the one-active-
session-per-user invariant, and GET /v1/history — all via httpx AsyncClient.
See api/CLAUDE.md → Test Structure.
"""

import logging

import pytest
from sqlalchemy import delete, select

from app.models.product import Product
from app.models.session_item import SessionItem
from app.models.shopping_session import ShoppingSession
from app.models.store_price import StorePrice
from app.repositories.user_repo import UserRepository
from app.routers import history as history_router
from app.routers import sessions as sessions_router

# Local Postgres persists between test runs (unlike CI's fresh container per run) —
# clean up this session's user/sessions/items/products after every run.
_TEST_PHONE = "+919876543230"
_TEST_BARCODE_1 = "6666666666666"
_TEST_BARCODE_2 = "7777777777777"
_UNKNOWN_BARCODE = "9999999999998"


@pytest.fixture(autouse=True)
def _stub_open_food_facts(monkeypatch):
    """Integration tests must never hit the real Open Food Facts API."""

    class _StubClient:
        async def lookup(self, barcode: str) -> dict | None:
            return None

    monkeypatch.setattr(sessions_router, "OpenFoodFactsClient", _StubClient)
    monkeypatch.setattr(history_router, "OpenFoodFactsClient", _StubClient)


@pytest.fixture(autouse=True)
async def _cleanup(db_session):
    yield
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_phone(_TEST_PHONE)
    if user is not None:
        session_ids = (
            await db_session.execute(select(ShoppingSession.id).where(ShoppingSession.user_id == user.id))
        ).scalars().all()
        if session_ids:
            await db_session.execute(delete(SessionItem).where(SessionItem.session_id.in_(session_ids)))
            await db_session.execute(delete(ShoppingSession).where(ShoppingSession.user_id == user.id))
        await db_session.delete(user)
    for barcode in (_TEST_BARCODE_1, _TEST_BARCODE_2):
        product = (await db_session.execute(select(Product).where(Product.barcode == barcode))).scalar_one_or_none()
        if product is not None:
            await db_session.execute(delete(StorePrice).where(StorePrice.product_id == product.id))
            await db_session.delete(product)
    await db_session.commit()


async def _auth_headers(client, caplog) -> dict[str, str]:
    with caplog.at_level(logging.INFO):
        await client.post("/v1/auth/send-otp", json={"phone": _TEST_PHONE})
    otp_records = [r for r in caplog.records if r.name == "app.services.auth_service"]
    otp = otp_records[-1].getMessage().split(": ")[-1]
    response = await client.post("/v1/auth/verify-otp", json={"phone": _TEST_PHONE, "otp": otp})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_session_then_add_item_updates_running_total(client, caplog):
    headers = await _auth_headers(client, caplog)
    await client.post("/v1/products", json={"barcode": _TEST_BARCODE_1, "name": "Parle-G", "price_paise": 1000})

    create_response = await client.post(
        "/v1/sessions", json={"store_name_text": "DMart Koramangala", "budget_paise": 50000}, headers=headers
    )
    assert create_response.status_code == 201
    session = create_response.json()
    assert session["status"] == "active"
    assert session["estimated_total_paise"] == 0

    add_response = await client.post(
        f"/v1/sessions/{session['id']}/items", json={"barcode": _TEST_BARCODE_1, "quantity": 2}, headers=headers
    )
    assert add_response.status_code == 201
    body = add_response.json()
    assert body["estimated_total_paise"] == 2000
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2
    assert body["items"][0]["line_total_paise"] == 2000


async def test_cannot_create_second_active_session(client, caplog):
    headers = await _auth_headers(client, caplog)
    first = await client.post(
        "/v1/sessions", json={"store_name_text": "Store A", "budget_paise": 10000}, headers=headers
    )
    assert first.status_code == 201

    second = await client.post(
        "/v1/sessions", json={"store_name_text": "Store B", "budget_paise": 10000}, headers=headers
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "SESSION_ALREADY_ACTIVE"


async def test_update_item_quantity_then_delete_item(client, caplog):
    headers = await _auth_headers(client, caplog)
    await client.post("/v1/products", json={"barcode": _TEST_BARCODE_2, "name": "Tata Salt", "price_paise": 2500})
    session = (
        await client.post("/v1/sessions", json={"store_name_text": "Store C", "budget_paise": 10000}, headers=headers)
    ).json()
    add_response = await client.post(
        f"/v1/sessions/{session['id']}/items", json={"barcode": _TEST_BARCODE_2, "quantity": 1}, headers=headers
    )
    item_id = add_response.json()["items"][0]["id"]

    update_response = await client.patch(
        f"/v1/sessions/{session['id']}/items/{item_id}", json={"quantity": 3}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["estimated_total_paise"] == 7500

    delete_response = await client.delete(f"/v1/sessions/{session['id']}/items/{item_id}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["items"] == []
    assert delete_response.json()["estimated_total_paise"] == 0


async def test_add_item_unknown_barcode_returns_product_not_found(client, caplog):
    headers = await _auth_headers(client, caplog)
    session = (
        await client.post("/v1/sessions", json={"store_name_text": "Store D", "budget_paise": 10000}, headers=headers)
    ).json()

    response = await client.post(
        f"/v1/sessions/{session['id']}/items", json={"barcode": _UNKNOWN_BARCODE}, headers=headers
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


async def test_finish_session_then_reject_further_mutation(client, caplog):
    headers = await _auth_headers(client, caplog)
    session = (
        await client.post("/v1/sessions", json={"store_name_text": "Store E", "budget_paise": 10000}, headers=headers)
    ).json()

    finish_response = await client.post(f"/v1/sessions/{session['id']}/finish", headers=headers)
    assert finish_response.status_code == 200
    assert finish_response.json()["status"] == "finished"

    finish_again = await client.post(f"/v1/sessions/{session['id']}/finish", headers=headers)
    assert finish_again.status_code == 409
    assert finish_again.json()["error"]["code"] == "SESSION_ALREADY_FINISHED"

    add_after_finish = await client.post(
        f"/v1/sessions/{session['id']}/items", json={"barcode": _UNKNOWN_BARCODE}, headers=headers
    )
    assert add_after_finish.status_code == 409
    assert add_after_finish.json()["error"]["code"] == "SESSION_ALREADY_FINISHED"


async def test_get_history_returns_finished_session(client, caplog):
    headers = await _auth_headers(client, caplog)
    session = (
        await client.post("/v1/sessions", json={"store_name_text": "Store F", "budget_paise": 10000}, headers=headers)
    ).json()
    await client.post(f"/v1/sessions/{session['id']}/finish", headers=headers)

    history_response = await client.get("/v1/history", headers=headers)
    assert history_response.status_code == 200
    body = history_response.json()
    assert body["total"] >= 1
    matching = [s for s in body["sessions"] if s["id"] == session["id"]]
    assert len(matching) == 1
    assert matching[0]["status"] == "finished"


async def test_get_session_without_auth_is_rejected(client):
    response = await client.get("/v1/sessions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 403


async def test_get_nonexistent_session_returns_404(client, caplog):
    headers = await _auth_headers(client, caplog)
    response = await client.get("/v1/sessions/00000000-0000-0000-0000-000000000000", headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"
