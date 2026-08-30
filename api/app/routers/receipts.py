"""Receipt routes — MVP stubs return 501, real implementation in R2.
See progress.md → Backend — MVP Stubs and CLAUDE.md §3.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/v1/receipts", tags=["receipts"])
