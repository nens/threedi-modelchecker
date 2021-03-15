"""Initial migration

Revision ID: 0001
Revises:
Create Date: 2021-02-15 16:31:00.792077

"""
from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0200"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "v2_connection_nodes", sa.Column("id", sa.Integer, primary_key=True)
    )


def downgrade():
    op.drop_table("v2_connection_nodes")
