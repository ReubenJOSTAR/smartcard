"""Store routes — MVP stub returns 501, real implementation (PostGIS discovery) in R3.
See api/CLAUDE.md → Stub as 501 in MVP.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/v1/stores", tags=["stores"])
