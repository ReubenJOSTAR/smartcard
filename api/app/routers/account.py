"""Account routes — MVP stub returns 501, real implementation (DPDP hard delete) in R2.
See progress.md → Backend — MVP Stubs.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/v1/account", tags=["account"])
