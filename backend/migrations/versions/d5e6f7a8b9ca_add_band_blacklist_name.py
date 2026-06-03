"""Add nullable name column to band_blacklist

Captured at delete time so curator audits (and the checked-in JSON) read
human-scannably without round-tripping each MBID through MusicBrainz.

Revision ID: d5e6f7a8b9ca
Revises: c3d4e5f6a7b9
Create Date: 2026-06-02
"""
import sqlalchemy as sa
from alembic import op

revision = "d5e6f7a8b9ca"
down_revision = "c3d4e5f6a7b9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band_blacklist", sa.Column("name", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("band_blacklist", "name")
