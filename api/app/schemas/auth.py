"""Auth request/response schemas — placeholder. See progress.md → Backend — Auth."""

from pydantic import BaseModel


class SendOTPRequest(BaseModel):
    pass


class VerifyOTPRequest(BaseModel):
    pass


class TokenResponse(BaseModel):
    pass
