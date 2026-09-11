"""StorePrice model.

`source` and `confidence_score` are non-nullable from day one (MVP only populates
'open_food_facts' | 'manual'; 'receipt_ocr' arrives in R2) — see CLAUDE.md §3.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StorePrice(Base):
    __tablename__ = "store_prices"
    __table_args__ = (
        # Postgres treats NULL as distinct from NULL for uniqueness purposes, so a
        # single UniqueConstraint(product_id, store_id) would silently allow duplicate
        # rows whenever store_id is NULL — the common MVP case, since real Store rows
        # don't exist until R3. Two partial unique indexes close that gap: one for a
        # real store, one for "no store yet".
        Index(
            "uq_store_price_product_with_store",
            "product_id",
            "store_id",
            unique=True,
            postgresql_where=text("store_id IS NOT NULL"),
        ),
        Index(
            "uq_store_price_product_no_store",
            "product_id",
            unique=True,
            postgresql_where=text("store_id IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    store_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.30)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
