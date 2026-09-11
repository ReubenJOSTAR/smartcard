"""Auth request/response schemas."""

from pydantic import BaseModel, Field

E164_PATTERN = r"^\+[1-9]\d{7,14}$"


class SendOTPRequest(BaseModel):
    phone: str = Field(pattern=E164_PATTERN, description="E.164 phone number, e.g. +919876543210")


class SendOTPResponse(BaseModel):
    message: str


class VerifyOTPRequest(BaseModel):
    phone: str = Field(pattern=E164_PATTERN)
    otp: str = Field(pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
