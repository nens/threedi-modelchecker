"""Create all tables if they do not exist already.

Revision ID: 0200
Revises:
Create Date: 2021-02-15 16:31:00.792077

"""
from alembic import op
from sqlalchemy.engine.reflection import Inspector

import geoalchemy2
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0200"
down_revision = None
branch_labels = None
depends_on = None

existing_tables = []


def _get_existing_tables():
    """Fill the global 'existing_tables'"""
    global existing_tables
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()


def create_table_if_not_exists(table_name, *args, **kwargs):
    """Create a table if it is not in the global 'existing_tables'"""
    if table_name in existing_tables:
        return
    else:
        return op.create_table(table_name, *args, **kwargs)


def upgrade():
    # Setup the global 'existing_tables'
    _get_existing_tables()
    # Initialize the Spatialite if necessary:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite" and "spatial_ref_sys" not in existing_tables:
        op.execute("SELECT InitSpatialMetadata()")
    create_table_if_not_exists(
        "v2_2d_boundary_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("timeseries", sa.Text(), nullable=True),
        sa.Column("boundary_type", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_2d_lateral",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("timeseries", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_calculation_point",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_type_id", sa.Integer(), nullable=True),
        sa.Column("user_ref", sa.String(length=80), nullable=False),
        sa.Column("calc_type", sa.Integer(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_connection_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("storage_area", sa.Float(), nullable=True),
        sa.Column("initial_waterlevel", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "the_geom_linestring",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_delta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("measure_delta", sa.String(length=50), nullable=True),
        sa.Column("measure_dt", sa.Float(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_value", sa.String(length=50), nullable=True),
        sa.Column("action_time", sa.Float(), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_measure_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_memory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("upper_threshold", sa.Float(), nullable=True),
        sa.Column("lower_threshold", sa.Float(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_value", sa.String(length=50), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_inverse", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_pid",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("setpoint", sa.Float(), nullable=True),
        sa.Column("kp", sa.Float(), nullable=True),
        sa.Column("ki", sa.Float(), nullable=True),
        sa.Column("kd", sa.Float(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_upper_limit", sa.String(length=50), nullable=True),
        sa.Column("target_lower_limit", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_table",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_table", sa.Text(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("measure_operator", sa.String(length=2), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_timed",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_table", sa.Text(), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_cross_section_definition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("width", sa.String(length=255), nullable=True),
        sa.Column("height", sa.String(length=255), nullable=True),
        sa.Column("shape", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_dem_average_area",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_floodfill",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("waterlevel", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_grid_refinement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("refinement_level", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_grid_refinement_area",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("refinement_level", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_groundwater",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("groundwater_impervious_layer_level", sa.Float(), nullable=True),
        sa.Column(
            "groundwater_impervious_layer_level_file",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "groundwater_impervious_layer_level_type", sa.Integer(), nullable=True
        ),
        sa.Column("phreatic_storage_capacity", sa.Float(), nullable=True),
        sa.Column(
            "phreatic_storage_capacity_file", sa.String(length=255), nullable=True
        ),
        sa.Column("phreatic_storage_capacity_type", sa.Integer(), nullable=True),
        sa.Column("equilibrium_infiltration_rate", sa.Float(), nullable=True),
        sa.Column(
            "equilibrium_infiltration_rate_file", sa.String(length=255), nullable=True
        ),
        sa.Column("equilibrium_infiltration_rate_type", sa.Integer(), nullable=True),
        sa.Column("initial_infiltration_rate", sa.Float(), nullable=True),
        sa.Column(
            "initial_infiltration_rate_file", sa.String(length=255), nullable=True
        ),
        sa.Column("initial_infiltration_rate_type", sa.Integer(), nullable=True),
        sa.Column("infiltration_decay_period", sa.Float(), nullable=True),
        sa.Column(
            "infiltration_decay_period_file", sa.String(length=255), nullable=True
        ),
        sa.Column("infiltration_decay_period_type", sa.Integer(), nullable=True),
        sa.Column("groundwater_hydro_connectivity", sa.Float(), nullable=True),
        sa.Column(
            "groundwater_hydro_connectivity_file", sa.String(length=255), nullable=True
        ),
        sa.Column("groundwater_hydro_connectivity_type", sa.Integer(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("leakage", sa.Float(), nullable=True),
        sa.Column("leakage_file", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_impervious_surface",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("surface_inclination", sa.String(length=64), nullable=False),
        sa.Column("surface_class", sa.String(length=128), nullable=False),
        sa.Column("surface_sub_class", sa.String(length=128), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("nr_of_inhabitants", sa.Float(), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("dry_weather_flow", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_interflow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interflow_type", sa.Integer(), nullable=False),
        sa.Column("porosity", sa.Float(), nullable=True),
        sa.Column("porosity_file", sa.String(length=255), nullable=True),
        sa.Column("porosity_layer_thickness", sa.Float(), nullable=True),
        sa.Column("impervious_layer_elevation", sa.Float(), nullable=True),
        sa.Column("hydraulic_conductivity", sa.Float(), nullable=True),
        sa.Column("hydraulic_conductivity_file", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_levee",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("crest_level", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("material", sa.Integer(), nullable=True),
        sa.Column("max_breach_depth", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_numerical_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cfl_strictness_factor_1d", sa.Float(), nullable=True),
        sa.Column("cfl_strictness_factor_2d", sa.Float(), nullable=True),
        sa.Column("convergence_cg", sa.Float(), nullable=True),
        sa.Column("convergence_eps", sa.Float(), nullable=True),
        sa.Column("flow_direction_threshold", sa.Float(), nullable=True),
        sa.Column("frict_shallow_water_correction", sa.Integer(), nullable=True),
        sa.Column("general_numerical_threshold", sa.Float(), nullable=True),
        sa.Column("integration_method", sa.Integer(), nullable=True),
        sa.Column("limiter_grad_1d", sa.Integer(), nullable=True),
        sa.Column("limiter_grad_2d", sa.Integer(), nullable=True),
        sa.Column("limiter_slope_crossectional_area_2d", sa.Integer(), nullable=True),
        sa.Column("limiter_slope_friction_2d", sa.Integer(), nullable=True),
        sa.Column("max_nonlin_iterations", sa.Integer(), nullable=True),
        sa.Column("max_degree", sa.Integer(), nullable=False),
        sa.Column("minimum_friction_velocity", sa.Float(), nullable=True),
        sa.Column("minimum_surface_area", sa.Float(), nullable=True),
        sa.Column("precon_cg", sa.Integer(), nullable=True),
        sa.Column("preissmann_slot", sa.Float(), nullable=True),
        sa.Column("pump_implicit_ratio", sa.Float(), nullable=True),
        sa.Column("thin_water_layer_definition", sa.Float(), nullable=True),
        sa.Column("use_of_cg", sa.Integer(), nullable=False),
        sa.Column("use_of_nested_newton", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_obstacle",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("crest_level", sa.Float(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_simple_infiltration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("infiltration_rate", sa.Float(), nullable=True),
        sa.Column("infiltration_rate_file", sa.String(length=255), nullable=True),
        sa.Column("infiltration_surface_option", sa.Integer(), nullable=True),
        sa.Column("max_infiltration_capacity_file", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_surface_parameters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("outflow_delay", sa.Float(), nullable=False),
        sa.Column("surface_layer_thickness", sa.Float(), nullable=False),
        sa.Column("infiltration", sa.Boolean(), nullable=False),
        sa.Column("max_infiltration_capacity", sa.Float(), nullable=False),
        sa.Column("min_infiltration_capacity", sa.Float(), nullable=False),
        sa.Column("infiltration_decay_constant", sa.Float(), nullable=False),
        sa.Column("infiltration_recovery_constant", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_1d_boundary_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("boundary_type", sa.Integer(), nullable=False),
        sa.Column("timeseries", sa.Text(), nullable=True),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_node_id"),
    )
    create_table_if_not_exists(
        "v2_1d_lateral",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.Column("timeseries", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_channel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_connected_pnt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("calculation_pnt_id", sa.Integer(), nullable=False),
        sa.Column("levee_id", sa.Integer(), nullable=True),
        sa.Column("exchange_level", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("control_group_id", sa.Integer(), nullable=True),
        sa.Column("measure_group_id", sa.Integer(), nullable=True),
        sa.Column("control_type", sa.String(length=15), nullable=True),
        sa.Column("control_id", sa.Integer(), nullable=True),
        sa.Column("start", sa.String(length=50), nullable=True),
        sa.Column("end", sa.String(length=50), nullable=True),
        sa.Column("measure_frequency", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_measure_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_group_id", sa.Integer(), nullable=True),
        sa.Column("object_type", sa.String(length=100), nullable=True),
        sa.Column("object_id", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_culvert",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=True),
        sa.Column("friction_value", sa.Float(), nullable=False),
        sa.Column("friction_type", sa.Integer(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("discharge_coefficient_positive", sa.Float(), nullable=True),
        sa.Column("discharge_coefficient_negative", sa.Float(), nullable=True),
        sa.Column("invert_level_start_point", sa.Float(), nullable=False),
        sa.Column("invert_level_end_point", sa.Float(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
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
        sa.Column(
            "initial_groundwater_level_file", sa.String(length=255), nullable=True
        ),
        sa.Column("initial_groundwater_level_type", sa.Integer(), nullable=True),
        sa.Column("numerical_settings_id", sa.Integer(), nullable=False),
        sa.Column("interflow_settings_id", sa.Integer(), nullable=True),
        sa.Column("control_group_id", sa.Integer(), nullable=True),
        sa.Column("simple_infiltration_settings_id", sa.Integer(), nullable=True),
        sa.Column("groundwater_settings_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_impervious_surface_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.Column("impervious_surface_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_manhole",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("shape", sa.String(length=4), nullable=True),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("length", sa.Float(), nullable=True),
        sa.Column("surface_level", sa.Float(), nullable=True),
        sa.Column("bottom_level", sa.Float(), nullable=False),
        sa.Column("drain_level", sa.Float(), nullable=True),
        sa.Column("sediment_level", sa.Float(), nullable=True),
        sa.Column("manhole_indicator", sa.Integer(), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=True),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_orifice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("crest_type", sa.Integer(), nullable=False),
        sa.Column("crest_level", sa.Float(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=True),
        sa.Column("friction_type", sa.Integer(), nullable=True),
        sa.Column("discharge_coefficient_positive", sa.Float(), nullable=True),
        sa.Column("discharge_coefficient_negative", sa.Float(), nullable=True),
        sa.Column("sewerage", sa.Boolean(), nullable=False),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_pipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("profile_num", sa.Integer(), nullable=True),
        sa.Column("sewerage_type", sa.Integer(), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=False),
        sa.Column("invert_level_start_point", sa.Float(), nullable=False),
        sa.Column("invert_level_end_point", sa.Float(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=False),
        sa.Column("friction_type", sa.Integer(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=True),
        sa.Column("material", sa.Integer(), nullable=True),
        sa.Column("original_length", sa.Float(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_pumpstation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("classification", sa.Integer(), nullable=True),
        sa.Column("sewerage", sa.Boolean(), nullable=True),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("start_level", sa.Float(), nullable=False),
        sa.Column("lower_stop_level", sa.Float(), nullable=False),
        sa.Column("upper_stop_level", sa.Float(), nullable=True),
        sa.Column("capacity", sa.Float(), nullable=False),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_surface",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("nr_of_inhabitants", sa.Float(), nullable=True),
        sa.Column("dry_weather_flow", sa.Float(), nullable=True),
        sa.Column("function", sa.String(length=64), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("surface_parameters_id", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_surface_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("surface_type", sa.String(length=40), nullable=False),
        sa.Column("surface_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_weir",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("crest_level", sa.Float(), nullable=False),
        sa.Column("crest_type", sa.Integer(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=True),
        sa.Column("friction_type", sa.Integer(), nullable=True),
        sa.Column("discharge_coefficient_positive", sa.Float(), nullable=True),
        sa.Column("discharge_coefficient_negative", sa.Float(), nullable=True),
        sa.Column("sewerage", sa.Boolean(), nullable=True),
        sa.Column("external", sa.Boolean(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_aggregation_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("global_settings_id", sa.Integer(), nullable=True),
        sa.Column("var_name", sa.String(length=100), nullable=False),
        sa.Column("flow_variable", sa.String(length=100), nullable=False),
        sa.Column("aggregation_method", sa.String(length=100), nullable=True),
        sa.Column("aggregation_in_space", sa.Boolean(), nullable=False),
        sa.Column("timestep", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_cross_section_location",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("reference_level", sa.Float(), nullable=False),
        sa.Column("friction_type", sa.Integer(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=False),
        sa.Column("bank_level", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_windshielding",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("north", sa.Float(), nullable=True),
        sa.Column("northeast", sa.Float(), nullable=True),
        sa.Column("east", sa.Float(), nullable=True),
        sa.Column("southeast", sa.Float(), nullable=True),
        sa.Column("south", sa.Float(), nullable=True),
        sa.Column("southwest", sa.Float(), nullable=True),
        sa.Column("west", sa.Float(), nullable=True),
        sa.Column("northwest", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    pass
