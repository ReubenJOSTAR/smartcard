"""Config model — single-row table (id=1), never insert additional rows.
See api/CLAUDE.md → Database Rules and → App Config Endpoint.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Config(Base):
    __tablename__ = "config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    min_app_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    latest_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    force_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    maintenance_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
