"""Removed unused columns.

Revision ID: 0201
Revises:
Create Date: 2021-09-29 13:50:19.544275

"""
from alembic import op

import geoalchemy2
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0203"
down_revision = "0202"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("v2_aggregation_settings") as batch_op:
        batch_op.drop_column("aggregation_in_space")
    with op.batch_alter_table("v2_connection_nodes") as batch_op:
        batch_op.drop_column("the_geom_linestring")


def downgrade():
    with op.batch_alter_table("v2_aggregation_settings") as batch_op:
        batch_op.add_column(
            sa.Column("aggregation_in_space", sa.Boolean(), nullable=False),
        )
    with op.batch_alter_table("v2_connection_nodes") as batch_op:
        batch_op.add_column(
            sa.Column(
                "the_geom_linestring",
                geoalchemy2.types.Geometry(
                    geometry_type="LINESTRING",
                    srid=4326,
                    management=True,
                ),
                nullable=True,
            ),
        )
