"""Add allowlisted_at column to band

Sticky curator override: when set, the seed leaves `auto_flagged` alone so a
band a human has vouched for doesn't get re-flagged on every re-seed. Backfill
existing rows that already carry an `inclusion_reason` — those are bands a
curator vouched for before this column existed.

Revision ID: d6f7a8b9cadb
Revises: c5e6f7a8b9ca
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op

revision = "d6f7a8b9cadb"
down_revision = "c5e6f7a8b9ca"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band", sa.Column("allowlisted_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(
        "UPDATE band SET allowlisted_at = NOW() "
        "WHERE inclusion_reason IS NOT NULL AND allowlisted_at IS NULL"
    )


def downgrade():
    op.drop_column("band", "allowlisted_at")
