"""breach and exchange

Revision ID: 0213
Revises: 0212
Create Date: 2022-12-21 14:54:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "0213"
down_revision = "0212"
branch_labels = None
depends_on = None


DROP_NON_DISPLACED = """
DELETE FROM v2_connected_pnt WHERE v2_connected_pnt.calculation_pnt_id IS NULL;
DELETE FROM v2_connected_pnt
  WHERE NOT EXISTS
    (SELECT 1 FROM v2_calculation_point
     WHERE v2_calculation_point.id = v2_connected_pnt.calculation_pnt_id);
DELETE FROM v2_connected_pnt
  WHERE v2_connected_pnt.id IN (
    SELECT v2_connected_pnt.id FROM v2_connected_pnt
    JOIN v2_calculation_point ON v2_connected_pnt.calculation_pnt_id = v2_calculation_point.id
    WHERE v2_connected_pnt.the_geom = v2_calculation_point.the_geom
  );
DELETE FROM v2_calculation_point
  WHERE NOT EXISTS
    (SELECT 1 FROM v2_connected_pnt
     WHERE v2_connected_pnt.calculation_pnt_id = v2_calculation_point.id);
"""


def clean_connected_points(connection):
    for q in DROP_NON_DISPLACED.split(";"):
        connection.execute(q)


def upgrade():
    conn = op.get_bind()

    clean_connected_points(conn)


def downgrade():
    pass
