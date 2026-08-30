"""StorePrice model.

`source` and `confidence_score` are non-nullable from day one (MVP only populates
'open_food_facts' | 'manual'; 'receipt_ocr' arrives in R2) — see CLAUDE.md §3.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StorePrice(Base):
    __tablename__ = "store_prices"
    __table_args__ = (UniqueConstraint("product_id", "store_id", name="uq_store_price_product_store"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    store_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.30)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
