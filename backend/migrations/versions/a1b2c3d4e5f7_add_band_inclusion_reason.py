"""Add inclusion_reason to band (curator note for off-genre outliers)

Nullable text column. Null = no curator note (default for the vast majority of
bands); non-null = a short explanation of why a band adjacent to / off the
hardcore-punk genre is included anyway (e.g. "included for split LP with X").

Revision ID: a1b2c3d4e5f7
Revises: f1a2b3c4d5e6
Create Date: 2026-06-01
"""
import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band", sa.Column("inclusion_reason", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("band", "inclusion_reason")
