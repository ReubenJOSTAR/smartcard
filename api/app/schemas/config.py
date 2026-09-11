"""App config response schema. See api/CLAUDE.md → App Config Endpoint."""

from pydantic import BaseModel, ConfigDict


class ConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    min_app_version: str
    latest_version: str
    force_update: bool
    maintenance_mode: bool
    maintenance_message: str | None
