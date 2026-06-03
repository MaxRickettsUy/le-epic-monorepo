"""Add band_blacklist table

MBIDs in this table are skipped by seed.mb_dump on subsequent runs, so a
curator's decision to remove an off-genre band sticks across re-seeds.

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-06-01
"""
import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b9"
down_revision = "b2c3d4e5f6a8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "band_blacklist",
        sa.Column("mbid", sa.String(length=36), primary_key=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("band_blacklist")
