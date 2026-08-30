"""Receipt model — empty for R2 per CLAUDE.md §3 (create now, implement later).
See progress.md → Backend — Core → "Also create Receipt + ReceiptLineItem models".
"""

from app.models.base import Base


class Receipt(Base):
    __tablename__ = "receipts"
