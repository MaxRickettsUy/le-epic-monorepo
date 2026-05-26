"""add logo column to Band

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-05-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('band', schema=None) as batch_op:
        batch_op.add_column(sa.Column('logo', sa.String(length=150), nullable=True))


def downgrade():
    with op.batch_alter_table('band', schema=None) as batch_op:
        batch_op.drop_column('logo')
