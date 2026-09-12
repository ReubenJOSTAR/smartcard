"""Account routes — MVP stub returns 501, real implementation (DPDP hard delete)
lands in R2. See root CLAUDE.md §14 and api/CLAUDE.md → "Stub as 501 in MVP".
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_id

router = APIRouter(prefix="/v1/account", tags=["account"])


@router.delete("")
async def delete_account(user_id: str = Depends(get_current_user_id)) -> None:
    raise HTTPException(
        status_code=501,
        detail={"code": "NOT_IMPLEMENTED", "message": "Account deletion coming in R2", "details": {}},
    )
