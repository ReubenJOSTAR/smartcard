"""Integration tests: full OTP send + verify flow via httpx AsyncClient.
See api/CLAUDE.md → Test Structure.
"""

import logging

import pytest

from app.repositories.user_repo import UserRepository

# Local Postgres persists between test runs (unlike CI's fresh container per run), so
# a user created by an earlier run would make the create-vs-lookup branch in
# UserRepository look permanently uncovered. Clean up these phones after every run.
_TEST_PHONES = ["+919876543220", "+919876543221", "+919876543222", "+919876543223"]


@pytest.fixture(autouse=True)
async def _cleanup_test_users(db_session):
    yield
    user_repo = UserRepository(db_session)
    for phone in _TEST_PHONES:
        user = await user_repo.get_by_phone(phone)
        if user is not None:
            await db_session.delete(user)
    await db_session.commit()


async def test_send_otp_returns_ack(client):
    response = await client.post("/v1/auth/send-otp", json={"phone": "+919876543220"})
    assert response.status_code == 200
    assert response.json() == {"message": "OTP sent"}


async def test_send_otp_rejects_invalid_phone(client):
    response = await client.post("/v1/auth/send-otp", json={"phone": "9876543220"})
    assert response.status_code == 422


async def test_full_otp_login_flow_issues_tokens(client, caplog, db_session):
    phone = "+919876543221"

    with caplog.at_level(logging.INFO):
        send_response = await client.post("/v1/auth/send-otp", json={"phone": phone})
    assert send_response.status_code == 200

    # Other loggers (httpx, sqlalchemy) also emit at INFO in this block, so filter by
    # logger name rather than assuming the dev OTP line is the last record captured.
    otp_records = [r for r in caplog.records if r.name == "app.services.auth_service"]
    otp = otp_records[-1].getMessage().split(": ")[-1]

    verify_response = await client.post("/v1/auth/verify-otp", json={"phone": phone, "otp": otp})
    assert verify_response.status_code == 200
    body = verify_response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]

    user = await UserRepository(db_session).get_by_phone(phone)
    assert user is not None


async def test_verify_otp_wrong_code_returns_401(client):
    phone = "+919876543222"
    await client.post("/v1/auth/send-otp", json={"phone": phone})

    response = await client.post("/v1/auth/verify-otp", json={"phone": phone, "otp": "000000"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "OTP_INVALID"


async def test_verify_otp_without_send_returns_expired(client):
    response = await client.post("/v1/auth/verify-otp", json={"phone": "+919876543223", "otp": "123456"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "OTP_EXPIRED"
