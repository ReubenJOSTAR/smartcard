"""ReceiptLineItem model — minimum viable columns for R2. Full OCR match fields
(product_name, actual_price, matched_product_id) land when R2 is actually built.
See progress.md → Backend — Core and CLAUDE.md §3.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReceiptLineItem(Base):
    __tablename__ = "receipt_line_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("receipts.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
