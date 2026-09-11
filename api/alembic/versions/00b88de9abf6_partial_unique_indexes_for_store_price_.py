"""partial unique indexes for store price no-store case

Revision ID: 00b88de9abf6
Revises: 85d56e67b258
Create Date: 2026-09-10 22:44:57.153425

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '00b88de9abf6'
down_revision = '85d56e67b258'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Postgres treats NULL as distinct from NULL for uniqueness, so the original
    # UniqueConstraint(product_id, store_id) silently allowed duplicate rows whenever
    # store_id is NULL — the common MVP case before real Store rows exist (R3). Replace
    # it with two partial unique indexes that actually enforce "one price per product
    # per store, and at most one price per product with no store yet".
    op.drop_constraint("uq_store_price_product_store", "store_prices", type_="unique")
    op.create_index(
        "uq_store_price_product_with_store",
        "store_prices",
        ["product_id", "store_id"],
        unique=True,
        postgresql_where=sa.text("store_id IS NOT NULL"),
    )
    op.create_index(
        "uq_store_price_product_no_store",
        "store_prices",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("store_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_store_price_product_no_store", table_name="store_prices")
    op.drop_index("uq_store_price_product_with_store", table_name="store_prices")
    op.create_unique_constraint("uq_store_price_product_store", "store_prices", ["product_id", "store_id"])
