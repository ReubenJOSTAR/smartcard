"""Receipt routes — MVP stubs return 501, real implementation lands in R2.
The routes exist now so the mobile client can be written against them from day
one — no client changes needed when R2 ships. See root CLAUDE.md §3 and
api/CLAUDE.md → "Stub as 501 in MVP".
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_id

router = APIRouter(prefix="/v1/receipts", tags=["receipts"])


def _not_implemented(message: str) -> HTTPException:
    return HTTPException(status_code=501, detail={"code": "NOT_IMPLEMENTED", "message": message, "details": {}})


@router.post("")
async def upload_receipt(user_id: str = Depends(get_current_user_id)) -> None:
    raise _not_implemented("Receipt upload coming in R2")


@router.get("/{receipt_id}")
async def get_receipt(receipt_id: uuid.UUID, user_id: str = Depends(get_current_user_id)) -> None:
    raise _not_implemented("Receipt OCR coming in R2")


@router.patch("/{receipt_id}/items/{item_id}")
async def correct_receipt_item(
    receipt_id: uuid.UUID, item_id: uuid.UUID, user_id: str = Depends(get_current_user_id)
) -> None:
    raise _not_implemented("Receipt line item correction coming in R2")
