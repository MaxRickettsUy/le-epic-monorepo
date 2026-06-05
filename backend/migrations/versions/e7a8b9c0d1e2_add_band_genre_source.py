"""Add source column to band_genre

Records the provenance of each band↔genre link: "mb" (MusicBrainz artist_tag,
the default for every pre-existing row) or an enrichment provider such as
"lastfm". NOT NULL with a server_default of "mb" so existing rows backfill to
the historical source without a data migration. The seed reads this to let
enrichment links rescue bands from the off-genre auto-flag.

Revision ID: e7a8b9c0d1e2
Revises: d6f7a8b9cadb
Create Date: 2026-06-04
"""
import sqlalchemy as sa
from alembic import op

revision = "e7a8b9c0d1e2"
down_revision = "d6f7a8b9cadb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "band_genre",
        sa.Column("source", sa.String(20), nullable=False, server_default="mb"),
    )


def downgrade():
    op.drop_column("band_genre", "source")
