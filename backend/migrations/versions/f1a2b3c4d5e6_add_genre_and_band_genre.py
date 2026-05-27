"""Add genre + band_genre (curated sub-genres)

Creates the curated sub-genre vocabulary cache and its band association.
Tables start empty; rows are populated by the seed (see plans/subgenres.md).

Revision ID: f1a2b3c4d5e6
Revises: b7c8d9e0f1a2
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None

NOW = sa.text("now()")


def upgrade():
    op.create_table(
        "genre",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    op.create_index("ix_genre_slug", "genre", ["slug"], unique=True)

    op.create_table(
        "band_genre",
        sa.Column(
            "band_id",
            sa.Integer(),
            sa.ForeignKey("band.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "genre_id",
            sa.Integer(),
            sa.ForeignKey("genre.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("vote_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )
    # Composite PK leads with band_id; index genre_id for facet/similarity lookups.
    op.create_index("ix_band_genre_genre_id", "band_genre", ["genre_id"])


def downgrade():
    op.drop_index("ix_band_genre_genre_id", table_name="band_genre")
    op.drop_table("band_genre")
    op.drop_index("ix_genre_slug", table_name="genre")
    op.drop_table("genre")
