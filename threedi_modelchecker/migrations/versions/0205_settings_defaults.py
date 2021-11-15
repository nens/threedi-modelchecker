"""make settings nullable

Revision ID: 0205
Revises: 0204
Create Date: 2021-11-15 16:41:43.316599

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0205'
down_revision = '0204'
branch_labels = None
depends_on = None


def global_settings_table():
    return sa.table(
        "v2_global_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("use_2d_flow", sa.Boolean(), nullable=False),
        sa.Column("use_1d_flow", sa.Boolean(), nullable=False),
        sa.Column("manhole_storage_area", sa.Float(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("sim_time_step", sa.Float(), nullable=False),
        sa.Column("output_time_step", sa.Float(), nullable=True),
        sa.Column("nr_timesteps", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Text(), nullable=False),
        sa.Column("grid_space", sa.Float(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=False),
        sa.Column("kmax", sa.Integer(), nullable=False),
        sa.Column("guess_dams", sa.Integer(), nullable=True),
        sa.Column("table_step_size", sa.Float(), nullable=False),
        sa.Column("flooding_threshold", sa.Float(), nullable=False),
        sa.Column("advection_1d", sa.Integer(), nullable=False),
        sa.Column("advection_2d", sa.Integer(), nullable=False),
        sa.Column("dem_file", sa.String(length=255), nullable=True),
        sa.Column("frict_type", sa.Integer(), nullable=True),
        sa.Column("frict_coef", sa.Float(), nullable=False),
        sa.Column("frict_coef_file", sa.String(length=255), nullable=True),
        sa.Column("water_level_ini_type", sa.Integer(), nullable=True),
        sa.Column("initial_waterlevel", sa.Float(), nullable=False),
        sa.Column("initial_waterlevel_file", sa.String(length=255), nullable=True),
        sa.Column("interception_global", sa.Float(), nullable=True),
        sa.Column("interception_file", sa.String(length=255), nullable=True),
        sa.Column("dem_obstacle_detection", sa.Boolean(), nullable=False),
        sa.Column("dem_obstacle_height", sa.Float(), nullable=True),
        sa.Column("embedded_cutoff_threshold", sa.Float(), nullable=True),
        sa.Column("epsg_code", sa.Integer(), nullable=True),
        sa.Column("timestep_plus", sa.Boolean(), nullable=False),
        sa.Column("max_angle_1d_advection", sa.Float(), nullable=True),
        sa.Column("minimum_sim_time_step", sa.Float(), nullable=True),
        sa.Column("maximum_sim_time_step", sa.Float(), nullable=True),
        sa.Column("frict_avg", sa.Integer(), nullable=True),
        sa.Column("wind_shielding_file", sa.String(length=255), nullable=True),
        sa.Column("use_0d_inflow", sa.Integer(), nullable=True),
        sa.Column("table_step_size_1d", sa.Float(), nullable=True),
        sa.Column("table_step_size_volume_2d", sa.Float(), nullable=True),
        sa.Column("use_2d_rain", sa.Integer(), nullable=False),
        sa.Column("initial_groundwater_level", sa.Float(), nullable=True),
        sa.Column("initial_groundwater_level_file", sa.String(length=255), nullable=True),
        sa.Column("initial_groundwater_level_type", sa.Integer(), nullable=True),
        sa.Column("numerical_settings_id", sa.Integer(), nullable=False),
        sa.Column("interflow_settings_id", sa.Integer(), nullable=True),
        sa.Column("control_group_id", sa.Integer(), nullable=True),
        sa.Column("simple_infiltration_settings_id", sa.Integer(), nullable=True),
        sa.Column("groundwater_settings_id", sa.Integer(), nullable=True),
    )


def upgrade():
    table = global_settings_table()
    op.execute(
        table.update()
        .where(table.c.output_time_step.is_(None))
        .values({"output_time_step": table.c.sim_time_step})
    )
    op.execute(
        table.update()
        .where(table.c.minimum_sim_time_step.is_(None))
        .values({"minimum_sim_time_step": table.c.sim_time_step})
    )
    op.execute(
        table.update()
        .where(table.c.maximum_sim_time_step.is_(None) & table.c.timestep_plus.is_(True))
        .values({"maximum_sim_time_step": table.c.sim_time_step})
    )
    op.execute(
        table.update()
        .where(table.c.frict_type.is_(None))
        .values({"frict_type": op.inline_literal(2)})
    )
    op.execute(
        table.update()
        .where(table.c.frict_avg.notin_((0, 1)))
        .values({"frict_avg": op.inline_literal(1)})
    )
    op.execute(
        table.update()
        .where(table.c.use_0d_inflow.is_(None))
        .values({"use_0d_inflow": op.inline_literal(0)})
    )


def downgrade():
    pass
