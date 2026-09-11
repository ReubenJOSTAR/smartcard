"""Import every model so Base.metadata (and therefore FK string resolution, e.g.
ShoppingSession.store_id -> ForeignKey("stores.id")) is always fully populated,
regardless of which route/module happens to run first. Mirrors alembic/env.py's
import list, which needed the same thing for autogenerate.
"""

from app.models.config import Config  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.receipt import Receipt  # noqa: F401
from app.models.receipt_line_item import ReceiptLineItem  # noqa: F401
from app.models.session_item import SessionItem  # noqa: F401
from app.models.shopping_session import ShoppingSession  # noqa: F401
from app.models.store import Store  # noqa: F401
from app.models.store_price import StorePrice  # noqa: F401
from app.models.user import User  # noqa: F401
