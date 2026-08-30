"""ShoppingSession model — placeholder. See progress.md → Backend — Core → "SQLAlchemy models".

NOTE (CLAUDE.md §3): must include `store_id` (nullable FK, for R3) and
`store_name_text` (MVP free-text) columns when implemented — do not retrofit later.
"""

from app.models.base import Base


class ShoppingSession(Base):
    __tablename__ = "shopping_sessions"
