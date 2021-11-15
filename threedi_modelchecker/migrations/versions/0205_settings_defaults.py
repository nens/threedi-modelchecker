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


NUMERICAL_SETTINGS_DEFAULTS = {
    "cfl_strictness_factor_1d": 1.0,
    "cfl_strictness_factor_2d": 1.0,
    "flow_direction_threshold": 1e-05,
    "convergence_cg": 1e-09,
    "convergence_eps": 1e-05,
    "frict_shallow_water_correction": 0,
    "general_numerical_threshold": 1e-08,
    "integration_method": 0,
    "limiter_grad_1d": 1,
    "limiter_grad_2d": 1,
    "limiter_slope_crossectional_area_2d": 0,
    "limiter_slope_friction_2d": 0,
    "max_nonlin_iterations": 20,
    "max_degree": 20,
    "minimum_friction_velocity": 0.01,
    "minimum_surface_area": 1e-08,
    "precon_cg": 1,
    "preissmann_slot": 0.0,
    "pump_implicit_ratio": 1.0,
    "thin_water_layer_definition": 0.01,
    "use_of_cg": 20,
    "use_of_nested_newton": 1,
}


GLOBAL_SETTINGS_DEFAULTS = {
    "frict_type": 2,
    "use_0d_inflow": 0,
}


def upgrade():
    for c, v in GLOBAL_SETTINGS_DEFAULTS.items():
        op.execute(
            f"UPDATE v2_global_settings SET {c} = {v} WHERE {c} IS NULL OR {c} < 0"
        )

    for c, v in NUMERICAL_SETTINGS_DEFAULTS.items():
        op.execute(f"UPDATE v2_numerical_settings SET {c} = {v} WHERE {c} IS NULL")

    op.execute(
        "UPDATE v2_global_settings SET minimum_sim_time_step = min(0.1, sim_time_step) WHERE minimum_sim_time_step IS NULL"
    )
    op.execute(
        "UPDATE v2_global_settings SET maximum_sim_time_step = max(1, sim_time_step) WHERE maximum_sim_time_step IS NULL"
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


def downgrade():
    pass
