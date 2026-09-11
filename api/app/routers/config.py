"""App config route — no auth required. See api/CLAUDE.md → App Config Endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.config_repo import ConfigRepository
from app.schemas.config import ConfigResponse

router = APIRouter(prefix="/v1", tags=["config"])


@router.get("/config", response_model=ConfigResponse)
async def get_config(db: AsyncSession = Depends(get_db)) -> ConfigResponse:
    config = await ConfigRepository(db).get()
    if config is None:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": "Config row missing", "details": {}},
        )
    return ConfigResponse.model_validate(config)
