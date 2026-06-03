"""Add raw MB tag snapshot column to band

Persists every MusicBrainz tag vote on the band as JSON (list of
{name, votes} sorted by votes desc), so curators can audit the source
signal without re-querying the MB dump. The curated `band_genre` links
only keep tags that map to the curated vocabulary; this column keeps
everything.

Revision ID: c4d5e6f7a8b9
Revises: d5e6f7a8b9ca
Create Date: 2026-06-02
"""
import sqlalchemy as sa
from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = "d5e6f7a8b9ca"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band", sa.Column("mb_tags", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("band", "mb_tags")
