"""Auth routes — OTP send/verify. See api/CLAUDE.md → OTP & Auth Flow."""

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.auth import SendOTPRequest, SendOTPResponse, TokenResponse, VerifyOTPRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(
    body: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SendOTPResponse:
    await AuthService(db, redis).send_otp(body.phone)
    return SendOTPResponse(message="OTP sent")


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_route(
    body: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    tokens = await AuthService(db, redis).verify_otp(body.phone, body.otp)
    return TokenResponse(**tokens)
