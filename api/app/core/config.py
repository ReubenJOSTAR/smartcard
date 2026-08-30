"""Pydantic Settings config — single source of truth for app configuration."""

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

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:8081,http://localhost:19006"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
