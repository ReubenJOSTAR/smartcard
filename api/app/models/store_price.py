"""StorePrice model — placeholder. See progress.md → Backend — Core → "SQLAlchemy models".

NOTE (CLAUDE.md §3): must include `source` (non-nullable, e.g. 'open_food_facts' |
'receipt_ocr' | 'manual') and `confidence_score` columns when implemented —
do not retrofit later.
"""

from app.models.base import Base


class StorePrice(Base):
    __tablename__ = "store_prices"
