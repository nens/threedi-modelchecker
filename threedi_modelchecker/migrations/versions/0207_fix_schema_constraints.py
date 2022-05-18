"""fix schema constraints

Revision ID: 0207
Revises: 0206
Create Date: 2022-05-18 10:15:20.851968

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0207'
down_revision = '0206'
branch_labels = None
depends_on = None


MIGRATION_QUERIES = """
DELETE FROM v2_grid_refinement WHERE (refinement_level IS NULL) OR (the_geom IS NULL);

DELETE FROM v2_grid_refinement_area WHERE (refinement_level IS NULL) OR (the_geom IS NULL);

UPDATE v2_orifice SET sewerage = NULL WHERE sewerage NOT IN (0, 1);
UPDATE v2_pumpstation SET sewerage = NULL WHERE sewerage NOT IN (0, 1);
UPDATE v2_weir SET sewerage = NULL WHERE sewerage NOT IN (0, 1);

UPDATE v2_weir SET external = NULL WHERE external NOT IN (0, 1);

UPDATE v2_connection_nodes SET the_geom_linestring = NULL;
"""


def upgrade():
    with op.batch_alter_table("v2_orifice") as batch_op:
        batch_op.alter_column("sewerage", nullable=True)

    with op.batch_alter_table("v2_pumpstation") as batch_op:
        batch_op.alter_column("sewerage", nullable=True)

    with op.batch_alter_table("v2_weir") as batch_op:
        batch_op.alter_column("sewerage", nullable=True)
        batch_op.alter_column("external", nullable=True)

    for q in MIGRATION_QUERIES.split(";"):
        op.execute(q)


def downgrade():
    pass
