"""Config model (single-row table) — placeholder. See progress.md → Backend — Core → "SQLAlchemy models"."""

from app.models.base import Base


class Config(Base):
    __tablename__ = "config"
