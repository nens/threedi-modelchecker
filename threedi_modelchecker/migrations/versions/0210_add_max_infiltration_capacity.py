"""add max_infiltration_capacity

Revision ID: 0209
Revises: 0208
Create Date: 2022-10-13 10:45

"""
from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0210"
down_revision = "0209"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("v2_simple_infiltration") as batch_op:
        batch_op.add_column(
            sa.Column("max_infiltration_capacity", sa.Float(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("v2_simple_infiltration") as batch_op:
        batch_op.drop_column("max_infiltration_capacity")
