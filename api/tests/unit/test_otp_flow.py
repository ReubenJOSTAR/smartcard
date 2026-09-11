"""Unit tests: OTP hashing and AuthService rate-limit/lockout logic.
See api/CLAUDE.md → OTP & Auth Flow.
"""

import pytest
from fastapi import HTTPException

from app.core.redis import redis_pool
from app.core.security import hash_otp, verify_otp
from app.services.auth_service import OTP_MAX_ATTEMPTS, OTP_SEND_LIMIT, AuthService


def test_hash_otp_is_deterministic():
    assert hash_otp("123456") == hash_otp("123456")


def test_hash_otp_differs_per_input():
    assert hash_otp("123456") != hash_otp("654321")


def test_verify_otp_accepts_matching_code():
    hashed = hash_otp("123456")
    assert verify_otp("123456", hashed) is True


def test_verify_otp_rejects_wrong_code():
    hashed = hash_otp("123456")
    assert verify_otp("000000", hashed) is False


@pytest.fixture
def auth_service(db_session):
    return AuthService(db_session, redis_pool)


async def test_send_otp_rate_limited_after_max_requests(auth_service):
    phone = "+919876543210"
    for _ in range(OTP_SEND_LIMIT):
        await auth_service.send_otp(phone)

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.send_otp(phone)
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["code"] == "OTP_RATE_LIMITED"


async def test_verify_otp_expired_when_no_code_sent(auth_service):
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_otp("+919876543211", "123456")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "OTP_EXPIRED"


async def test_verify_otp_locks_out_after_max_attempts(auth_service):
    phone = "+919876543212"
    await auth_service.send_otp(phone)

    for _ in range(OTP_MAX_ATTEMPTS):
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.verify_otp(phone, "000000")
        assert exc_info.value.detail["code"] == "OTP_INVALID"

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.verify_otp(phone, "000000")
    assert exc_info.value.status_code == 429
    assert exc_info.value.detail["code"] == "OTP_LOCKED_OUT"
