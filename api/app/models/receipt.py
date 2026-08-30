"""Receipt model — minimum viable columns for R2. `session_id` is nullable and
`ocr_status` defaults to "pending" since nothing populates these yet; full receipt
upload/OCR fields (image_s3_key, actual_total) land when R2 is actually built.
See progress.md → Backend — Core and CLAUDE.md §3.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("shopping_sessions.id"), index=True, nullable=True
    )
    ocr_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
