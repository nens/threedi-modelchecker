"""make settings nullable

Revision ID: 0205
Revises: 0204
Create Date: 2021-11-15 16:41:43.316599

"""
from alembic import op

import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0205"
down_revision = "0204"
branch_labels = None
depends_on = None


GLOBAL_SETTINGS_DEFAULTS = {
    "frict_type": 2,
    "use_0d_inflow": 0,
}


def upgrade():
    op.execute(
        "UPDATE v2_global_settings SET frict_type = 2 WHERE frict_type IS NULL"
    )
    op.execute(
        "UPDATE v2_global_settings SET use_0d_inflow = 0 WHERE use_0d_inflow IS NULL"
    )
    op.execute(
        "UPDATE v2_global_settings SET minimum_sim_time_step = min(0.1, sim_time_step) WHERE minimum_sim_time_step IS NULL OR minimum_time_step <= 0"
    )
    op.execute(
        "UPDATE v2_global_settings SET maximum_sim_time_step = max(1, sim_time_step) WHERE maximum_sim_time_step IS NULL AND timestep_plus = 1"
    )
    op.execute(
        "UPDATE v2_global_settings SET output_time_step = max(1, sim_time_step) WHERE output_time_step IS NULL"
    )
    op.execute(
        "UPDATE v2_global_settings SET flooding_threshold = 1e-6 WHERE flooding_threshold IS NULL OR flooding_threshold < 0"
    )
    op.execute(
        "UPDATE v2_global_settings SET frict_avg = 1 WHERE frict_avg NOT IN (0, 1)"
    )
    op.execute(
        "UPDATE v2_global_settings SET max_angle_1d_advection = 1.256637 WHERE max_angle_1d_advection = 90"
    )
    op.execute(
        "UPDATE v2_global_settings SET dist_calc_points = 100 WHERE dist_calc_points <= 0"
    )
    op.execute(
        "UPDATE v2_global_settings SET dem_obstacle_detection = 0 WHERE dem_obstacle_detection = ''"
    )
    op.execute(
        "UPDATE v2_global_settings SET table_step_size_1d = NULL WHERE table_step_size_1d <= 0"
    )
    op.execute(
        "UPDATE v2_global_settings SET table_step_size_volume_2d = NULL WHERE table_step_size_volume_2d <= 0"
    )
    op.execute(
        "UPDATE v2_simple_infiltration SET infiltration_surface_option = 0 WHERE infiltration_surface_option IS NULL"
    )
    op.execute(
        "UPDATE v2_simple_infiltration SET infiltration_rate = 0 WHERE infiltration_rate < 0"
    )
    op.execute(
        "UPDATE v2_numerical_settings SET precon_cg = 1 WHERE precon_cg > 1"
    )


def downgrade():
    pass
