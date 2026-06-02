"""Add seed_share signals to band (outlier audit)

Three nullable columns populated by seed.mb_dump from the MusicBrainz tag
vote counts: how many votes the seed tag got, the total across all tags,
and the share. Lets /band/needs-review rank candidate outliers without
re-querying the MB dump.

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-06-01
"""
import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a8"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("band", sa.Column("seed_votes", sa.Integer(), nullable=True))
    op.add_column("band", sa.Column("total_tag_votes", sa.Integer(), nullable=True))
    op.add_column("band", sa.Column("seed_share", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("band", "seed_share")
    op.drop_column("band", "total_tag_votes")
    op.drop_column("band", "seed_votes")
