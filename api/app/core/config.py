"""Pydantic Settings config — placeholder. See progress.md → Backend — Core."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str

    # Redis — OTP storage only in MVP
    REDIS_URL: str

    # Auth
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_VERIFY_SERVICE_SID: str

    # App
    SECRET_KEY: str
    ENVIRONMENT: str
    MIN_APP_VERSION: str


settings: Settings
