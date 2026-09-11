"""Auth business logic — OTP send/verify, user provisioning, JWT issuance.
See api/CLAUDE.md → OTP & Auth Flow.
"""

import logging
import secrets

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_otp, verify_otp
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 600
OTP_SEND_LIMIT = 3
OTP_SEND_WINDOW_SECONDS = 3600
OTP_MAX_ATTEMPTS = 3
OTP_LOCKOUT_SECONDS = 3600


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self.db = db
        self.redis = redis
        self.user_repo = UserRepository(db)

    async def send_otp(self, phone: str) -> None:
        rate_key = f"otp:ratelimit:{phone}"
        request_count = await self.redis.incr(rate_key)
        if request_count == 1:
            await self.redis.expire(rate_key, OTP_SEND_WINDOW_SECONDS)
        if request_count > OTP_SEND_LIMIT:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "OTP_RATE_LIMITED",
                    "message": "Too many OTP requests — try again later",
                    "details": {},
                },
            )

        otp = f"{secrets.randbelow(1_000_000):06d}"
        # TODO(r2): send via Twilio Verify. No Twilio account configured yet, so the
        # dev/mock path below logs the code for local testing instead — gated to dev
        # only, since logging an OTP + phone number in plaintext is exactly what
        # root CLAUDE.md's "never log PII in plaintext" rule exists to prevent.
        if settings.ENVIRONMENT == "development":
            logger.info("Dev OTP for %s: %s", phone, otp)

        await self.redis.set(f"otp:code:{phone}", hash_otp(otp), ex=OTP_TTL_SECONDS)
        await self.redis.delete(f"otp:attempts:{phone}")

    async def verify_otp(self, phone: str, otp: str) -> dict[str, str]:
        stored_hash = await self.redis.get(f"otp:code:{phone}")
        if stored_hash is None:
            raise HTTPException(
                status_code=401,
                detail={"code": "OTP_EXPIRED", "message": "Code expired — request a new one", "details": {}},
            )

        attempts_key = f"otp:attempts:{phone}"
        attempts = int(await self.redis.get(attempts_key) or 0)
        if attempts >= OTP_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "OTP_LOCKED_OUT",
                    "message": "Too many attempts — try again in 1 hour",
                    "details": {},
                },
            )

        if not verify_otp(otp, stored_hash):
            new_attempts = await self.redis.incr(attempts_key)
            if new_attempts == 1:
                await self.redis.expire(attempts_key, OTP_LOCKOUT_SECONDS)
            raise HTTPException(
                status_code=401,
                detail={"code": "OTP_INVALID", "message": "Incorrect code", "details": {}},
            )

        await self.redis.delete(f"otp:code:{phone}", attempts_key)

        user = await self.user_repo.get_by_phone(phone)
        if user is None:
            user = await self.user_repo.create(phone)

        user_id = str(user.id)
        return {
            "access_token": create_access_token(user_id, phone),
            "refresh_token": create_refresh_token(user_id),
            "token_type": "bearer",
        }
