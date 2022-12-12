"""breach and exchange

Revision ID: 0212
Revises: 0211
Create Date: 2022-12-12 14:48:00

"""
from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0212"
down_revision = "0211"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("v2_exchange_line") as batch_op:
        batch_op.add_column(sa.Column("exchange_level", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("v2_exchange_line") as batch_op:
        batch_op.drop_column("exchange_level")
