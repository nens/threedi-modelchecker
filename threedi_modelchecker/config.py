from .checks.base import BaseCheck
from .checks.base import CheckLevel
from .checks.base import EnumCheck
from .checks.base import FileExistsCheck
from .checks.base import ForeignKeyCheck
from .checks.base import GeneralCheck
from .checks.base import GeometryCheck
from .checks.base import GeometryTypeCheck
from .checks.base import NotNullCheck
from .checks.base import QueryCheck
from .checks.base import RangeCheck
from .checks.base import TypeCheck
from .checks.base import UniqueCheck
from .checks.factories import generate_enum_checks
from .checks.factories import generate_foreign_key_checks
from .checks.factories import generate_geometry_checks
from .checks.factories import generate_geometry_type_checks
from .checks.factories import generate_not_null_checks
from .checks.factories import generate_type_checks
from .checks.factories import generate_unique_checks
from .checks.other import BankLevelCheck
from .checks.other import ConnectionNodesDistance
from .checks.other import ConnectionNodesLength
from .checks.other import CrossSectionShapeCheck
from .checks.other import OpenChannelsWithNestedNewton
from .checks.other import TimeseriesCheck
from .checks.other import Use0DFlowCheck
from .threedi_model import models
from .threedi_model.models import constants
from geoalchemy2 import functions as geo_func
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import Query
from typing import List


# some conditions that are used often
uses_0d_surfaces = models.GlobalSetting.use_0d_inflow == constants.InflowType.SURFACE
uses_0d_impervious_surfaces = (
    models.GlobalSetting.use_0d_inflow == constants.InflowType.IMPERVIOUS_SURFACE
)

CHEZY = constants.FrictionType.CHEZY.value
MANNING = constants.FrictionType.MANNING.value
BROAD_CRESTED = constants.CrestType.BROAD_CRESTED.value
SHORT_CRESTED = constants.CrestType.SHORT_CRESTED.value
CONNECTED_ALL = [
    constants.CalculationType.CONNECTED,
    constants.CalculationType.DOUBLE_CONNECTED,
]

FOREIGN_KEY_CHECKS: List[ForeignKeyCheck] = []
UNIQUE_CHECKS: List[UniqueCheck] = []
INVALID_TYPE_CHECKS: List[TypeCheck] = []
INVALID_GEOMETRY_CHECKS: List[GeometryCheck] = []
INVALID_GEOMETRY_TYPE_CHECKS: List[GeometryTypeCheck] = []
INVALID_ENUM_CHECKS: List[EnumCheck] = []

TIMESERIES_CHECKS: List[TimeseriesCheck] = [
    TimeseriesCheck(models.BoundaryCondition1D.timeseries),
    TimeseriesCheck(models.BoundaryConditions2D.timeseries),
    TimeseriesCheck(models.Lateral1d.timeseries),
    TimeseriesCheck(models.Lateral2D.timeseries),
]

RANGE_CHECKS: List[BaseCheck] = [
    RangeCheck(
        column=models.CrossSectionLocation.friction_value,
        filters=models.CrossSectionLocation.friction_type == CHEZY,
        min_value=0,
    ),
    RangeCheck(
        column=models.CrossSectionLocation.friction_value,
        filters=models.CrossSectionLocation.friction_type == MANNING,
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    ),
    RangeCheck(
        column=models.Culvert.friction_value,
        filters=models.Culvert.friction_type == CHEZY,
        min_value=0,
    ),
    RangeCheck(
        column=models.Culvert.friction_value,
        filters=models.Culvert.friction_type == MANNING,
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    ),
    RangeCheck(
        column=models.GroundWater.phreatic_storage_capacity,
        filters=models.GroundWater.global_settings != None,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        column=models.ImperviousSurface.area,
        min_value=0,
        filters=uses_0d_impervious_surfaces,
    ),
    RangeCheck(
        level=CheckLevel.WARNING,
        column=models.ImperviousSurface.dry_weather_flow,
        min_value=0,
        filters=uses_0d_impervious_surfaces,
    ),
    RangeCheck(
        column=models.ImperviousSurfaceMap.percentage,
        min_value=0,
        filters=uses_0d_impervious_surfaces,
    ),
    RangeCheck(
        column=models.Interflow.porosity,
        filters=models.Interflow.global_settings != None,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        column=models.Interflow.impervious_layer_elevation,
        filters=models.Interflow.global_settings != None,
        min_value=0,
    ),
    RangeCheck(
        column=models.Orifice.discharge_coefficient_negative,
        min_value=0,
    ),
    RangeCheck(
        column=models.Orifice.discharge_coefficient_positive,
        min_value=0,
    ),
    NotNullCheck(
        column=models.Orifice.friction_value,
        filters=(models.Orifice.crest_type == BROAD_CRESTED),
    ),
    NotNullCheck(
        column=models.Orifice.friction_type,
        filters=(models.Orifice.crest_type == BROAD_CRESTED),
    ),
    RangeCheck(
        column=models.Orifice.friction_value,
        filters=(
            (models.Orifice.friction_type == CHEZY)
            & (models.Orifice.crest_type == BROAD_CRESTED)
        ),
        min_value=0,
    ),
    RangeCheck(
        column=models.Orifice.friction_value,
        filters=(
            (models.Orifice.friction_type == MANNING)
            & (models.Orifice.crest_type == BROAD_CRESTED)
        ),
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    ),
    RangeCheck(
        column=models.Pipe.dist_calc_points,
        min_value=0,
        left_inclusive=False,  # 0 itself is not allowed
    ),
    RangeCheck(
        column=models.Pipe.friction_value,
        filters=models.Pipe.friction_type == CHEZY,
        min_value=0,
    ),
    RangeCheck(
        column=models.Pipe.friction_value,
        filters=models.Pipe.friction_type == MANNING,
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    ),
    GeneralCheck(
        column=models.Pumpstation.upper_stop_level,
        criterion_valid=and_(
            models.Pumpstation.upper_stop_level > models.Pumpstation.lower_stop_level,
            models.Pumpstation.upper_stop_level > models.Pumpstation.start_level,
        ),
    ),
    GeneralCheck(
        column=models.Pumpstation.lower_stop_level,
        criterion_valid=and_(
            models.Pumpstation.lower_stop_level < models.Pumpstation.start_level,
            models.Pumpstation.lower_stop_level < models.Pumpstation.upper_stop_level,
        ),
    ),
    GeneralCheck(
        column=models.Pumpstation.start_level,
        criterion_valid=and_(
            models.Pumpstation.start_level > models.Pumpstation.lower_stop_level,
            models.Pumpstation.start_level < models.Pumpstation.upper_stop_level,
        ),
    ),
    RangeCheck(
        column=models.Pumpstation.capacity,
        min_value=0,
    ),
    GeneralCheck(
        level=CheckLevel.WARNING,
        column=models.Pumpstation.capacity,
        criterion_invalid=models.Pumpstation.capacity == 0.0,
    ),
    RangeCheck(
        column=models.SimpleInfiltration.infiltration_rate,
        filters=models.SimpleInfiltration.global_settings != None,
        min_value=0,
    ),
    RangeCheck(
        column=models.Surface.nr_of_inhabitants,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.Surface.dry_weather_flow,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.Surface.area,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.SurfaceMap.percentage,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        level=CheckLevel.WARNING,
        column=models.SurfaceMap.percentage,
        max_value=100,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.SurfaceParameter.outflow_delay,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.SurfaceParameter.max_infiltration_capacity,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.SurfaceParameter.min_infiltration_capacity,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.SurfaceParameter.infiltration_decay_constant,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.SurfaceParameter.infiltration_recovery_constant,
        min_value=0,
        filters=uses_0d_surfaces,
    ),
    RangeCheck(
        column=models.Weir.discharge_coefficient_negative,
        min_value=0,
    ),
    RangeCheck(
        column=models.Weir.discharge_coefficient_positive,
        min_value=0,
    ),
    NotNullCheck(
        column=models.Weir.friction_value,
        filters=(models.Weir.crest_type == BROAD_CRESTED),
    ),
    NotNullCheck(
        column=models.Weir.friction_type,
        filters=(models.Weir.crest_type == BROAD_CRESTED),
    ),
    RangeCheck(
        column=models.Weir.friction_value,
        filters=(
            (models.Weir.friction_type == CHEZY)
            & (models.Weir.crest_type == BROAD_CRESTED)
        ),
        min_value=0,
    ),
    RangeCheck(
        column=models.Weir.friction_value,
        filters=(
            (models.Weir.friction_type == MANNING)
            & (models.Weir.crest_type == BROAD_CRESTED)
        ),
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    ),
    GeneralCheck(
        column=models.GlobalSetting.maximum_sim_time_step,
        criterion_valid=models.GlobalSetting.maximum_sim_time_step
        >= models.GlobalSetting.sim_time_step,
    ),
    GeneralCheck(
        column=models.GlobalSetting.sim_time_step,
        criterion_valid=models.GlobalSetting.sim_time_step
        >= models.GlobalSetting.minimum_sim_time_step,
    ),
]

OTHER_CHECKS: List[BaseCheck] = [
    BankLevelCheck(),
    CrossSectionShapeCheck(),
    # 1d boundary conditions cannot be connected to a pumpstation
    GeneralCheck(
        column=models.BoundaryCondition1D.connection_node_id,
        criterion_invalid=or_(
            models.BoundaryCondition1D.connection_node_id
            == models.Pumpstation.connection_node_start_id,
            models.BoundaryCondition1D.connection_node_id
            == models.Pumpstation.connection_node_end_id,
        ),
    ),
    Use0DFlowCheck(),
    OpenChannelsWithNestedNewton(),
    ConnectionNodesDistance(minimum_distance=0.001),
]


CONDITIONAL_CHECKS = [
    QueryCheck(
        column=models.ConnectionNode.storage_area,
        invalid=Query(models.ConnectionNode)
        .join(models.Manhole)
        .filter(models.ConnectionNode.storage_area < 0),
        message="The ConnectionNode.storage_area should be >= 0 "
        "when the ConnectionNode is a Manhole",
    ),
    QueryCheck(
        column=models.CrossSectionLocation.reference_level,
        invalid=Query(models.CrossSectionLocation).filter(
            models.CrossSectionLocation.bank_level != None,
            models.CrossSectionLocation.reference_level
            > models.CrossSectionLocation.bank_level,
        ),
        message="CrossSectionLocation.reference_level should be below the CrossSectionLocation.bank_level"
        "when CrossSectionLocation.bank_level is not null",
    ),
    QueryCheck(
        column=models.GlobalSetting.dem_obstacle_height,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.dem_obstacle_height <= 0,
            models.GlobalSetting.dem_obstacle_detection == True,
        ),
        message="GlobalSetting.dem_obstacle_height should be larger than 0 when "
        "GlobalSetting.dem_obstacle_detection == True",
    ),
    QueryCheck(
        column=models.GroundWater.equilibrium_infiltration_rate_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.equilibrium_infiltration_rate_type == None,
            models.GroundWater.equilibrium_infiltration_rate_file != None,
        ),
        message="The field GroundWater.equilibrium_infiltration_rate_type should be filled, when using "
        "GroundWater.equilibrium_infiltration_rate_file.",
    ),
    QueryCheck(
        column=models.GroundWater.infiltration_decay_period_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.infiltration_decay_period_type == None,
            models.GroundWater.infiltration_decay_period_type != None,
        ),
        message="The field GroundWater.infiltration_decay_period_type should be filled, when using"
        "GroundWater.infiltration_decay_period_type.",
    ),
    QueryCheck(
        column=models.GroundWater.groundwater_hydro_connectivity_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.groundwater_hydro_connectivity_type == None,
            models.GroundWater.groundwater_hydro_connectivity_file != None,
        ),
        message="The field GroundWater.groundwater_hydro_connectivity_type should be filled, when using "
        "GroundWater.groundwater_hydro_connectivity_file is not null",
    ),
    QueryCheck(
        column=models.GroundWater.groundwater_impervious_layer_level_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.groundwater_impervious_layer_level_type == None,
            models.GroundWater.groundwater_impervious_layer_level_file != None,
        ),
        message="The field GroundWater.groundwater_impervious_layer_level_type should be filled, when using"
        "when GroundWater.groundwater_impervious_layer_level_file",
    ),
    QueryCheck(
        column=models.GroundWater.initial_infiltration_rate_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.initial_infiltration_rate_type == None,
            models.GroundWater.initial_infiltration_rate_file != None,
        ),
        message="The field GroundWater.initial_infiltration_rate_type should be filled, when using "
        "GroundWater.initial_infiltration_rate_file",
    ),
    QueryCheck(
        column=models.GroundWater.phreatic_storage_capacity_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.initial_infiltration_rate_type == None,
            models.GroundWater.initial_infiltration_rate_file != None,
        ),
        message="The field GroundWater.phreatic_storage_capacity_type should be filled, when using "
        "GroundWater.phreatic_storage_capacity_file.",
    ),
    QueryCheck(
        column=models.Interflow.porosity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            models.Interflow.porosity == None,
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message=f"The field Interflow.porosity should be filled, when "
        f"Interflow.interflow_type != {constants.InterflowType.NO_INTERLFOW}",
    ),
    QueryCheck(
        column=models.Interflow.porosity_layer_thickness,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            models.Interflow.porosity_layer_thickness > 0,
            models.Interflow.interflow_type
            in [
                constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY,
                constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY,
            ],
        ),
        message=f"Interflow.porosity_layer_thickness should be filled and >0 in case "
        f"Interflow.interflow_type is "
        f"{constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY} or "
        f"{constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY}",
    ),
    QueryCheck(
        column=models.Interflow.impervious_layer_elevation,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            models.Interflow.impervious_layer_elevation == None,
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message=f"Interflow.impervious_layer_elevation cannot be null when "
        f"Interflow.interflow_type is not {constants.InterflowType.NO_INTERLFOW}",
    ),
    QueryCheck(
        column=models.Interflow.hydraulic_conductivity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            or_(
                models.Interflow.hydraulic_conductivity == None,
                models.Interflow.hydraulic_conductivity_file == None,
            ),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message=f"Interflow.hydraulic_conductivity cannot be null or "
        f"Interflow.hydraulic_conductivity_file cannot be null when "
        f"Interflow.interflow_type != {constants.InterflowType.NO_INTERLFOW}",
    ),
    QueryCheck(
        column=models.Channel.calculation_type,
        invalid=Query(models.Channel).filter(
            models.Channel.calculation_type.in_(
                [
                    constants.CalculationType.EMBEDDED,
                    constants.CalculationType.CONNECTED,
                    constants.CalculationType.DOUBLE_CONNECTED,
                ]
            ),
            (models.GlobalSetting.dem_file == None)
            | (models.GlobalSetting.dem_file == ""),
        ),
        message=f"Channel.calculation_type cannot be "
        f"{constants.CalculationType.EMBEDDED}, "
        f"{constants.CalculationType.CONNECTED} or "
        f"{constants.CalculationType.DOUBLE_CONNECTED} when "
        f"GlobalSetting.dem_file is null",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Pumpstation.lower_stop_level,
        invalid=Query(models.Pumpstation)
        .join(
            models.ConnectionNode,
            models.Pumpstation.connection_node_start_id == models.ConnectionNode.id,
        )
        .join(models.Manhole)
        .filter(
            models.Pumpstation.type_ == constants.PumpType.SUCTION_SIDE,
            models.Pumpstation.lower_stop_level <= models.Manhole.bottom_level,
        ),
        message="Pumpstation.lower_stop_level should be higher than "
        "Manhole.bottom_level. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Pumpstation.lower_stop_level,
        invalid=Query(models.Pumpstation)
        .join(
            models.ConnectionNode,
            models.Pumpstation.connection_node_end_id == models.ConnectionNode.id,
        )
        .join(models.Manhole)
        .filter(
            models.Pumpstation.type_ == constants.PumpType.DELIVERY_SIDE,
            models.Pumpstation.lower_stop_level <= models.Manhole.bottom_level,
        ),
        message="Pumpstation.lower_stop_level should be higher than "
        "Manhole.bottom_level. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Pipe.invert_level_end_point,
        invalid=Query(models.Pipe)
        .join(
            models.ConnectionNode,
            models.Pipe.connection_node_end_id == models.ConnectionNode.id,
        )
        .join(models.Manhole)
        .filter(
            models.Pipe.invert_level_end_point < models.Manhole.bottom_level,
        ),
        message="Pipe.invert_level_end_point should be higher than or equal to "
        "Manhole.bottom_level. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Pipe.invert_level_start_point,
        invalid=Query(models.Pipe)
        .join(
            models.ConnectionNode,
            models.Pipe.connection_node_start_id == models.ConnectionNode.id,
        )
        .join(models.Manhole)
        .filter(
            models.Pipe.invert_level_start_point < models.Manhole.bottom_level,
        ),
        message="Pipe.invert_level_start_point should be higher than or equal to "
        "Manhole.bottom_level. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Manhole.bottom_level,
        invalid=Query(models.Manhole).filter(
            models.Manhole.drain_level < models.Manhole.bottom_level,
            models.Manhole.calculation_type.in_(CONNECTED_ALL),
        ),
        message="Manhole.drain_level >= Manhole.bottom_level when "
        "Manhole.calculation_type is CONNECTED. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Manhole.drain_level,
        invalid=Query(models.Manhole).filter(
            (models.GlobalSetting.dem_file == None)
            | (models.GlobalSetting.dem_file == ""),
            models.GlobalSetting.manhole_storage_area > 0,
            models.Manhole.calculation_type.in_(CONNECTED_ALL),
            models.Manhole.drain_level == None,
        ),
        message="Manhole.drain_level cannot be null when using sub-basins (GlobalSettings.manhole_storage_area > 0) and no DEM is supplied.",
    ),
    QueryCheck(
        column=models.GlobalSetting.maximum_sim_time_step,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.timestep_plus == True,
            models.GlobalSetting.maximum_sim_time_step == None,
        ),
        message="GlobalSettings.maximum_sim_time_step cannot be null when "
        "GlobalSettings.timestep_plus is True",
    ),
    QueryCheck(
        column=models.GlobalSetting.use_1d_flow,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.use_1d_flow == False,
            Query(func.count(models.ConnectionNode.id) > 0).label("1d_count"),
        ),
        message="GlobalSettings.use_1d_flow must be set to True when there are 1D "
        "elements in the model",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Channel.id,
        invalid=Query(models.Channel).filter(
            geo_func.ST_Length(
                geo_func.ST_Transform(
                    models.Channel.the_geom,
                    Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code"),
                )
            )
            < 0.05
        ),
        message="Length of a channel geometry is very short (< 0.05 m). A length of at least 1.0 m is recommended.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Culvert.id,
        invalid=Query(models.Culvert).filter(
            geo_func.ST_Length(
                geo_func.ST_Transform(
                    models.Culvert.the_geom,
                    Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code"),
                )
            )
            < 0.05
        ),
        message="Length of a culvert geometry is very short (< 0.05 m). A length of at least 1.0 m is recommended.",
    ),
    ConnectionNodesLength(  # TO DO zie foutmelding hierover bij culverts, we willen een check distance en een advies distance
        level=CheckLevel.WARNING,
        column=models.Pipe.id,
        start_node=models.Pipe.connection_node_start,
        end_node=models.Pipe.connection_node_end,
        min_distance=0.05,
    ),
    ConnectionNodesLength(
        level=CheckLevel.WARNING,
        column=models.Weir.id,
        filters=models.Weir.crest_type == constants.CrestType.BROAD_CRESTED,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05,
    ),
    ConnectionNodesLength(
        level=CheckLevel.WARNING,
        column=models.Orifice.id,
        filters=models.Orifice.crest_type == constants.CrestType.BROAD_CRESTED,
        start_node=models.Orifice.connection_node_start,
        end_node=models.Orifice.connection_node_end,
        min_distance=0.05,
    ),
    QueryCheck(
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode).filter(
            models.ConnectionNode.id.notin_(
                Query(models.Pipe.connection_node_start_id).union_all(
                    Query(models.Pipe.connection_node_end_id),
                    Query(models.Channel.connection_node_start_id),
                    Query(models.Channel.connection_node_end_id),
                    Query(models.Culvert.connection_node_start_id),
                    Query(models.Culvert.connection_node_end_id),
                    Query(models.Weir.connection_node_start_id),
                    Query(models.Weir.connection_node_end_id),
                    Query(models.Pumpstation.connection_node_start_id),
                    Query(models.Pumpstation.connection_node_end_id),
                    Query(models.Orifice.connection_node_start_id),
                    Query(models.Orifice.connection_node_end_id),
                )
            )
        ),
        message="This is an individual ConnectionNode. Connect it to either a pipe, "
        "channel, culvert, weir, orifice or pumpstation.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        column=models.Pipe.id,
        invalid=Query(models.Pipe)
        .join(
            models.ConnectionNode,
            models.Pipe.connection_node_start_id == models.ConnectionNode.id,
        )
        .filter(
            models.Pipe.calculation_type == constants.PipeCalculationType.ISOLATED,
            models.ConnectionNode.storage_area.is_(None),
        )
        .union(
            Query(models.Pipe)
            .join(
                models.ConnectionNode,
                models.Pipe.connection_node_end_id == models.ConnectionNode.id,
            )
            .filter(
                models.Pipe.calculation_type == constants.PipeCalculationType.ISOLATED,
                models.ConnectionNode.storage_area.is_(None),
            )
        ),
        message="When connecting two isolated pipes, it is recommended to add storage to the connection node.",
    ),
    RangeCheck(
        column=models.NumericalSettings.convergence_eps,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        column=models.NumericalSettings.convergence_cg,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        column=models.NumericalSettings.general_numerical_threshold,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        column=models.NumericalSettings.flow_direction_threshold,
        min_value=0,
        left_inclusive=False,
    ),
]


FILE_EXISTS_CHECKS = [
    FileExistsCheck(column=models.GlobalSetting.dem_file),
    FileExistsCheck(column=models.GlobalSetting.frict_coef_file),
    FileExistsCheck(column=models.GlobalSetting.interception_file),
    FileExistsCheck(
        column=models.Interflow.porosity_file,
        filters=models.Interflow.global_settings != None,
    ),
    FileExistsCheck(
        column=models.Interflow.hydraulic_conductivity_file,
        filters=models.Interflow.global_settings != None,
    ),
    FileExistsCheck(
        column=models.SimpleInfiltration.infiltration_rate_file,
        filters=models.SimpleInfiltration.global_settings != None,
    ),
    FileExistsCheck(
        column=models.SimpleInfiltration.max_infiltration_capacity_file,
        filters=models.SimpleInfiltration.global_settings != None,
    ),
    FileExistsCheck(
        column=models.GroundWater.groundwater_hydro_connectivity_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        column=models.GroundWater.phreatic_storage_capacity_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        column=models.GroundWater.equilibrium_infiltration_rate_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        column=models.GroundWater.initial_infiltration_rate_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        column=models.GroundWater.infiltration_decay_period_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        column=models.GroundWater.groundwater_hydro_connectivity_file,
        filters=models.GroundWater.global_settings != None,
    ),
]


class Config:
    """Collection of checks

    Some checks are generated by a factory. These are usually very generic
    checks which apply to many columns, such as foreign keys."""

    def __init__(self, models):
        self.models = models
        self.checks = []
        self.generate_checks()

    def generate_checks(self):
        FOREIGN_KEY_CHECKS = []
        UNIQUE_CHECKS = []
        NOT_NULL_CHECKS = []
        INVALID_TYPE_CHECKS = []
        INVALID_GEOMETRY_CHECKS = []
        INVALID_GEOMETRY_TYPE_CHECKS = []
        INVALID_ENUM_CHECKS = []
        # Call the check factories:
        for model in self.models:
            FOREIGN_KEY_CHECKS += generate_foreign_key_checks(model.__table__)
            UNIQUE_CHECKS += generate_unique_checks(model.__table__)
            NOT_NULL_CHECKS += generate_not_null_checks(model.__table__)
            INVALID_TYPE_CHECKS += generate_type_checks(model.__table__)
            INVALID_GEOMETRY_CHECKS += generate_geometry_checks(model.__table__)
            INVALID_GEOMETRY_TYPE_CHECKS += generate_geometry_type_checks(
                model.__table__
            )
            INVALID_ENUM_CHECKS += generate_enum_checks(
                model.__table__,
                custom_level_map={
                    "sewerage_type": "INFO",
                    "zoom_category": "INFO",
                    "material": "INFO",
                },
            )

        self.checks += FOREIGN_KEY_CHECKS
        self.checks += UNIQUE_CHECKS
        self.checks += NOT_NULL_CHECKS
        self.checks += INVALID_TYPE_CHECKS
        self.checks += INVALID_GEOMETRY_CHECKS
        self.checks += INVALID_GEOMETRY_TYPE_CHECKS
        self.checks += INVALID_ENUM_CHECKS
        self.checks += OTHER_CHECKS
        self.checks += TIMESERIES_CHECKS
        self.checks += RANGE_CHECKS
        self.checks += CONDITIONAL_CHECKS
        self.checks += FILE_EXISTS_CHECKS
        return None

    def iter_checks(self, level=CheckLevel.ERROR):
        """Iterate over checks with at least 'level'"""
        level = CheckLevel.get(level)  # normalize
        for check in self.checks:
            if check.level >= level:
                yield check
