"""Unit tests: JWT creation/decoding and the get_current_user_id dependency.
See api/CLAUDE.md → OTP & Auth Flow.
"""

import jwt as pyjwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import create_access_token, create_refresh_token, decode_token, get_current_user_id


def test_access_token_round_trips_claims():
    token = create_access_token(user_id="abc-123", phone="+919876543210")
    payload = decode_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["phone"] == "+919876543210"
    assert payload["type"] == "access"


def test_refresh_token_has_no_phone_claim():
    token = create_refresh_token(user_id="abc-123")
    payload = decode_token(token)
    assert payload["sub"] == "abc-123"
    assert payload["type"] == "refresh"
    assert "phone" not in payload


def test_decode_token_rejects_garbage():
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_token("not-a-real-token")


async def test_get_current_user_id_accepts_valid_access_token():
    token = create_access_token(user_id="abc-123", phone="+919876543210")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert await get_current_user_id(credentials) == "abc-123"


async def test_get_current_user_id_rejects_refresh_token():
    token = create_refresh_token(user_id="abc-123")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(credentials)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "UNAUTHORIZED"


async def test_get_current_user_id_rejects_garbage_token():
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(credentials)
    assert exc_info.value.status_code == 401
