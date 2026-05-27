"""Add begin_year/end_year to band (years active)

Captures the band's formed/disbanded years, seeded from MusicBrainz
artist.begin_date_year / end_date_year. Both nullable (MB dates are often
year-only or absent).

Revision ID: b7c8d9e0f1a2
Revises: d4e5f6a7b8c9
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "b7c8d9e0f1a2"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band", sa.Column("begin_year", sa.Integer(), nullable=True))
    op.add_column("band", sa.Column("end_year", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("band", "end_year")
    op.drop_column("band", "begin_year")
