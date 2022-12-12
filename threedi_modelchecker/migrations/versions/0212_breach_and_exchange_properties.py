"""breach and exchange

Revision ID: 0211
Revises: 0210
Create Date: 2022-11-23 11:21:10.967235

"""
from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0211"
down_revision = "0210"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("v2_exchange_line") as batch_op:
        batch_op.add_column(sa.Column("exchange_level", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("v2_exchange_line") as batch_op:
        batch_op.drop_column("exchange_level")
