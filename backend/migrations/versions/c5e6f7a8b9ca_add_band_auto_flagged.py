"""Add auto_flagged column to band

Marks bands the seed's genre allowlist judged off-genre (MB tag votes exist
but none land in the curated `core` set). Nullable so existing rows can be
filled lazily by the next seed run; indexed because the review surface
filters on it.

Revision ID: c5e6f7a8b9ca
Revises: c4d5e6f7a8b9
Create Date: 2026-06-03
"""
import sqlalchemy as sa
from alembic import op

revision = "c5e6f7a8b9ca"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band", sa.Column("auto_flagged", sa.Boolean(), nullable=True))
    op.create_index("ix_band_auto_flagged", "band", ["auto_flagged"])


def downgrade():
    op.drop_index("ix_band_auto_flagged", table_name="band")
    op.drop_column("band", "auto_flagged")
