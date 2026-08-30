"""ShoppingSession model.

`store_id` is nullable in MVP (free-text store name); `store_name_text` is deprecated
once real Store selection ships in R3. See CLAUDE.md §3.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ShoppingSession(Base):
    __tablename__ = "shopping_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    store_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stores.id"), nullable=True)
    store_name_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
