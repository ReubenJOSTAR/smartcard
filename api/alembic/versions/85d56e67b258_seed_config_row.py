"""seed config row

Revision ID: 85d56e67b258
Revises: 0aa7d9ccca1a
Create Date: 2026-09-10 21:36:10.038189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85d56e67b258'
down_revision = '0aa7d9ccca1a'
branch_labels = None
depends_on = None


config_table = sa.table(
    "config",
    sa.column("id", sa.Integer),
    sa.column("min_app_version", sa.String),
    sa.column("latest_version", sa.String),
    sa.column("force_update", sa.Boolean),
    sa.column("maintenance_mode", sa.Boolean),
    sa.column("maintenance_message", sa.String),
)


def upgrade() -> None:
    # Config is a single-row table (id=1) — see api/CLAUDE.md → Database Rules.
    # GET /v1/config always reads this row, so it must exist from the first migration
    # forward rather than being lazily created by application code.
    op.bulk_insert(
        config_table,
        [
            {
                "id": 1,
                "min_app_version": "1.0.0",
                "latest_version": "1.0.0",
                "force_update": False,
                "maintenance_mode": False,
                "maintenance_message": None,
            }
        ],
    )


def downgrade() -> None:
    op.execute(config_table.delete().where(config_table.c.id == 1))
