"""Integration tests: MVP account route stub (DELETE /v1/account returns 501).
See api/CLAUDE.md → "Stub as 501 in MVP" and → Test Structure.
"""

import logging

import pytest
from sqlalchemy import delete

from app.models.shopping_session import ShoppingSession
from app.repositories.user_repo import UserRepository

_TEST_PHONE = "+919876543232"


@pytest.fixture(autouse=True)
async def _cleanup(db_session):
    yield
    user_repo = UserRepository(db_session)
    user = await user_repo.get_by_phone(_TEST_PHONE)
    if user is not None:
        await db_session.execute(delete(ShoppingSession).where(ShoppingSession.user_id == user.id))
        await db_session.delete(user)
    await db_session.commit()


async def _auth_headers(client, caplog) -> dict[str, str]:
    with caplog.at_level(logging.INFO):
        await client.post("/v1/auth/send-otp", json={"phone": _TEST_PHONE})
    otp_records = [r for r in caplog.records if r.name == "app.services.auth_service"]
    otp = otp_records[-1].getMessage().split(": ")[-1]
    response = await client.post("/v1/auth/verify-otp", json={"phone": _TEST_PHONE, "otp": otp})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_delete_account_returns_not_implemented(client, caplog):
    headers = await _auth_headers(client, caplog)
    response = await client.delete("/v1/account", headers=headers)
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"


async def test_delete_account_requires_auth(client):
    response = await client.delete("/v1/account")
    assert response.status_code == 403
