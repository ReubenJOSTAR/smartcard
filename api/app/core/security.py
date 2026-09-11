"""JWT creation/verification, OTP hashing, and the FastAPI dependency that
protects authenticated routes. See api/CLAUDE.md → OTP & Auth Flow.
"""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
REFRESH_TOKEN_EXPIRES = timedelta(days=30)

_bearer_scheme = HTTPBearer()


def create_access_token(user_id: str, phone: str) -> str:
    payload = {
        "sub": user_id,
        "phone": phone,
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRES,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRES,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])


def hash_otp(otp: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), otp.encode(), hashlib.sha256).hexdigest()


def verify_otp(otp: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_otp(otp), hashed)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """FastAPI dependency for protected routes — decodes the bearer token and
    returns the authenticated user's id, or raises a 401 in the project's
    standard error shape.
    """
    try:
        payload = decode_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Token expired", "details": {}},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token", "details": {}},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token type", "details": {}},
        )
    return payload["sub"]
