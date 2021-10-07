from .checks.base import BaseCheck
from .checks.base import CheckLevel
from .checks.base import FileExistsCheck
from .checks.base import GeneralCheck
from .checks.base import NotNullCheck
from .checks.base import QueryCheck
from .checks.base import RangeCheck
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
from .checks.other import CrossSectionLocationCheck
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


def is_none_or_empty(col):
    return (col == None) | (col == "")


CHECKS: List[BaseCheck] = []

## 002x: FRICTION
CHECKS += [
    RangeCheck(
        error_code=21,
        column=getattr(table, "friction_value"),
        filters=getattr(table, "friction_type") == constants.FrictionType.CHEZY.value,
        min_value=0,
    )
    for table in [
        models.CrossSectionLocation,
        models.Culvert,
        models.Pipe,
    ]
]
CHECKS += [
    RangeCheck(
        error_code=21,
        column=getattr(table, "friction_value"),
        filters=(getattr(table, "friction_type") == constants.FrictionType.CHEZY.value)
        & (getattr(table, "crest_type") == constants.CrestType.BROAD_CRESTED.value),
        min_value=0,
    )
    for table in [
        models.Orifice,
        models.Weir,
    ]
]
CHECKS += [
    RangeCheck(
        error_code=22,
        column=getattr(table, "friction_value"),
        filters=getattr(table, "friction_type") == constants.FrictionType.MANNING.value,
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    )
    for table in [
        models.CrossSectionLocation,
        models.Culvert,
        models.Pipe,
    ]
]
CHECKS += [
    RangeCheck(
        error_code=23,
        column=getattr(table, "friction_value"),
        filters=(
            getattr(table, "friction_type") == constants.FrictionType.MANNING.value
        )
        & (getattr(table, "crest_type") == constants.CrestType.BROAD_CRESTED.value),
        min_value=0,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
    )
    for table in [
        models.Orifice,
        models.Weir,
    ]
]
CHECKS += [
    NotNullCheck(
        error_code=24,
        column=getattr(table, "friction_value"),
        filters=getattr(table, "crest_type") == constants.CrestType.BROAD_CRESTED.value,
    )
    for table in [models.Orifice, models.Weir]
]
CHECKS += [
    NotNullCheck(
        error_code=25,
        column=getattr(table, "friction_type"),
        filters=getattr(table, "crest_type") == constants.CrestType.BROAD_CRESTED.value,
    )
    for table in [models.Orifice, models.Weir]
]


## 003x: CALCULATION TYPE

CHECKS += [
    QueryCheck(
        error_code=31,
        column=models.Channel.calculation_type,
        invalid=Query(models.Channel).filter(
            models.Channel.calculation_type.in_(
                [
                    constants.CalculationType.EMBEDDED,
                    constants.CalculationType.CONNECTED,
                    constants.CalculationType.DOUBLE_CONNECTED,
                ]
            ),
            is_none_or_empty(models.GlobalSetting.dem_file),
        ),
        message=f"Channel.calculation_type cannot be "
        f"{constants.CalculationType.EMBEDDED}, "
        f"{constants.CalculationType.CONNECTED} or "
        f"{constants.CalculationType.DOUBLE_CONNECTED} when "
        f"GlobalSetting.dem_file is null",
    )
]

## 004x: VARIOUS OBJECT SETTINGS
CHECKS += [
    RangeCheck(
        error_code=41,
        column=getattr(table, "discharge_coefficient_negative"),
        min_value=0,
    )
    for table in [models.Culvert, models.Weir, models.Orifice]
]
CHECKS += [
    RangeCheck(
        error_code=42,
        column=getattr(table, "discharge_coefficient_positive"),
        min_value=0,
    )
    for table in [models.Culvert, models.Weir, models.Orifice]
]
CHECKS += [
    RangeCheck(
        error_code=43,
        column=getattr(table, "dist_calc_points"),
        min_value=0,
        left_inclusive=False,  # 0 itself is not allowed
    )
    for table in [models.GlobalSetting, models.Channel, models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        error_code=44,
        column=models.ConnectionNode.storage_area,
        invalid=Query(models.ConnectionNode)
        .join(models.Manhole)
        .filter(models.ConnectionNode.storage_area < 0),
        message="The ConnectionNode.storage_area should be >= 0 when the ConnectionNode is a Manhole",
    ),
]


## 005x: CROSS SECTIONS

CHECKS += [
    CrossSectionShapeCheck(error_code=51),
    CrossSectionLocationCheck(error_code=52),
    OpenChannelsWithNestedNewton(error_code=53),
    QueryCheck(
        error_code=54,
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
        error_code=55,
        column=models.Channel.id,
        invalid=Query(models.Channel).filter(
            ~models.Channel.cross_section_locations.any()
        ),
        message="v2_channel has no cross section locations",
    ),
]

## 006x: PUMPSTATIONS

CHECKS += [
    GeneralCheck(
        error_code=61,
        column=models.Pumpstation.upper_stop_level,
        criterion_valid=and_(
            models.Pumpstation.upper_stop_level > models.Pumpstation.lower_stop_level,
            models.Pumpstation.upper_stop_level > models.Pumpstation.start_level,
        ),
    ),
    GeneralCheck(
        error_code=62,
        column=models.Pumpstation.lower_stop_level,
        criterion_valid=and_(
            models.Pumpstation.lower_stop_level < models.Pumpstation.start_level,
            models.Pumpstation.lower_stop_level < models.Pumpstation.upper_stop_level,
        ),
    ),
    GeneralCheck(
        error_code=63,
        column=models.Pumpstation.start_level,
        criterion_valid=and_(
            models.Pumpstation.start_level > models.Pumpstation.lower_stop_level,
            models.Pumpstation.start_level < models.Pumpstation.upper_stop_level,
        ),
    ),
    RangeCheck(
        error_code=64,
        column=models.Pumpstation.capacity,
        min_value=0,
    ),
    GeneralCheck(
        error_code=65,
        level=CheckLevel.WARNING,
        column=models.Pumpstation.capacity,
        criterion_invalid=models.Pumpstation.capacity == 0.0,
    ),
]

## 007x: BOUNDARY CONDITIONS

CHECKS += [
    # 1d boundary conditions cannot be connected to a pumpstation
    GeneralCheck(
        error_code=71,
        column=models.BoundaryCondition1D.connection_node_id,
        criterion_invalid=or_(
            models.BoundaryCondition1D.connection_node_id
            == models.Pumpstation.connection_node_start_id,
            models.BoundaryCondition1D.connection_node_id
            == models.Pumpstation.connection_node_end_id,
        ),
    ),
]


## 01xx: LEVEL CHECKS

CHECKS += [BankLevelCheck(error_code=101)]
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=102,
        column=getattr(table, "invert_level_start_point"),
        invalid=Query(table)
        .join(
            models.ConnectionNode,
            getattr(table, "connection_node_start_id") == models.ConnectionNode.id,
        )
        .join(models.Manhole)
        .filter(
            getattr(table, "invert_level_start_point") < models.Manhole.bottom_level,
        ),
        message=f"{table}.invert_level_start_point should be higher than or equal to Manhole.bottom_level. In the future, this will lead to an error.",
    )
    for table in [models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=103,
        column=getattr(table, "invert_level_end_point"),
        invalid=Query(table)
        .join(
            models.ConnectionNode,
            getattr(table, "connection_node_end_id") == models.ConnectionNode.id,
        )
        .join(models.Manhole)
        .filter(
            getattr(table, "invert_level_end_point") < models.Manhole.bottom_level,
        ),
        message=f"{table}.invert_level_end_point should be higher than or equal to Manhole.bottom_level. In the future, this will lead to an error.",
    )
    for table in [models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=104,
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
        error_code=105,
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
        error_code=106,
        column=models.Manhole.bottom_level,
        invalid=Query(models.Manhole).filter(
            models.Manhole.drain_level < models.Manhole.bottom_level,
            models.Manhole.calculation_type.in_(
                [constants.CalculationTypeNode.CONNECTED]
            ),
        ),
        message="Manhole.drain_level >= Manhole.bottom_level when "
        "Manhole.calculation_type is CONNECTED. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=107,
        column=models.Manhole.drain_level,
        invalid=Query(models.Manhole).filter(
            is_none_or_empty(models.GlobalSetting.dem_file),
            models.GlobalSetting.manhole_storage_area > 0,
            models.Manhole.calculation_type.in_(
                [constants.CalculationTypeNode.CONNECTED]
            ),
            models.Manhole.drain_level == None,
        ),
        message="Manhole.drain_level cannot be null when using sub-basins (v2_global_settings.manhole_storage_area > 0) and no DEM is supplied.",
    ),
]

## 020x: Spatial checks

CHECKS += [ConnectionNodesDistance(error_code=201, minimum_distance=0.001)]
CHECKS += [
    QueryCheck(
        error_code=202,
        level=CheckLevel.WARNING,
        column=getattr(table, "id"),
        invalid=Query(models.Channel).filter(
            geo_func.ST_Length(
                geo_func.ST_Transform(
                    getattr(table, "the_geom"),
                    Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code"),
                )
            )
            < 0.05
        ),
        message=f"Length of a {table} is very short (< 0.05 m). A length of at least 1.0 m is recommended.",
    )
    for table in [models.Channel, models.Culvert]
]
CHECKS += [
    ConnectionNodesLength(
        error_code=203,
        level=CheckLevel.WARNING,
        column=models.Pipe.id,
        start_node=models.Pipe.connection_node_start,
        end_node=models.Pipe.connection_node_end,
        min_distance=0.05,
    )
]
CHECKS += [
    ConnectionNodesLength(
        error_code=204,
        level=CheckLevel.WARNING,
        column=getattr(table, "id"),
        filters=getattr(table, "crest_type") == constants.CrestType.BROAD_CRESTED,
        start_node=getattr(table, "connection_node_start"),
        end_node=getattr(table, "connection_node_end"),
        min_distance=0.05,
    )
    for table in [models.Orifice, models.Weir]
]


## 025x: Connectivity

CHECKS += [
    QueryCheck(
        error_code=251,
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
        error_code=252,
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
]
CHECKS += [
    QueryCheck(
        error_code=253,
        column=table.connection_node_end_id,
        invalid=Query(table).filter(
            table.connection_node_start_id == table.connection_node_end_id
        ),
        message=f"a {table.__tablename__} cannot be connected to itself (connection_node_start_id must not equal connection_node_end_id)",
    )
    for table in (
        models.Channel,
        models.Culvert,
        models.Orifice,
        models.Pipe,
        models.Pumpstation,
        models.Weir,
    )
]


## 030x: SETTINGS

CHECKS += [
    QueryCheck(
        error_code=301,
        level=CheckLevel.WARNING,
        column=models.GlobalSetting.frict_type,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.frict_type == None
        ),
        message="The global friction type (v2_global_settings.friction_type) is not defined. In the future, this will lead to an error.",
    ),
    QueryCheck(
        error_code=302,
        column=models.GlobalSetting.dem_obstacle_height,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.dem_obstacle_height <= 0,
            models.GlobalSetting.dem_obstacle_detection == True,
        ),
        message="GlobalSetting.dem_obstacle_height should be larger than 0 when "
        "GlobalSetting.dem_obstacle_detection == True",
    ),
    QueryCheck(
        error_code=303,
        column=models.GlobalSetting.use_1d_flow,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.use_1d_flow == False,
            Query(func.count(models.ConnectionNode.id) > 0).label("1d_count"),
        ),
        message="v2_global_settings.use_1d_flow must be set to True when there are 1D "
        "elements in the model",
    ),
    QueryCheck(
        error_code=304,
        column=models.GlobalSetting.groundwater_settings_id,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.groundwater_settings_id != None,
            models.GlobalSetting.simple_infiltration_settings != None,
        ),
        message="simple_infiltration in combination with groundwater flow is not allowed.",
    ),
    RangeCheck(
        error_code=305,
        column=models.GlobalSetting.kmax,
        min_value=0,
        left_inclusive=False,  # 0 is not allowed
    ),
]

## 04xx: Groundwater, Interflow & Infiltration
CHECKS += [
    RangeCheck(
        error_code=401,
        column=models.Interflow.porosity,
        filters=models.Interflow.global_settings != None,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        error_code=402,
        column=models.Interflow.impervious_layer_elevation,
        filters=models.Interflow.global_settings != None,
        min_value=0,
    ),
    RangeCheck(
        error_code=403,
        column=models.SimpleInfiltration.infiltration_rate,
        filters=models.SimpleInfiltration.global_settings != None,
        min_value=0,
    ),
    QueryCheck(
        error_code=404,
        column=models.SimpleInfiltration.infiltration_rate,
        invalid=Query(models.SimpleInfiltration).filter(
            models.SimpleInfiltration.global_settings != None,
            models.SimpleInfiltration.infiltration_rate == None,
            is_none_or_empty(models.SimpleInfiltration.infiltration_rate_file),
        ),
        message="a global simple infiltration rate (v2_simple_infiltration.infiltration_rate) should be defined when not using a simple infiltration rate file.",
    ),
    QueryCheck(
        error_code=405,
        column=models.GroundWater.equilibrium_infiltration_rate,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.equilibrium_infiltration_rate == None,
            is_none_or_empty(
                models.GroundWater.equilibrium_infiltration_rate_file,
            ),
        ),
        message="a global equilibrium infiltration rate (v2_groundwater.equilibrium_infiltration_rate) should be defined when not using an equilibrium infiltration rate file.",
    ),
    QueryCheck(
        error_code=406,
        column=models.GroundWater.equilibrium_infiltration_rate_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.equilibrium_infiltration_rate_type == None,
            ~is_none_or_empty(models.GroundWater.equilibrium_infiltration_rate_file),
        ),
        message="an equilibrium infiltration rate type (v2_groundwater.equilibrium_infiltration_rate_type) should be defined when using an equilibrium infiltration rate file.",
    ),
    QueryCheck(
        error_code=407,
        column=models.GroundWater.infiltration_decay_period,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.infiltration_decay_period == None,
            is_none_or_empty(models.GroundWater.infiltration_decay_period_file),
        ),
        message="a global infiltration decay period (v2_groundwater.infiltration_decay_period) should be defined when not using an infiltration decay period file.",
    ),
    QueryCheck(
        error_code=408,
        column=models.GroundWater.infiltration_decay_period_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.infiltration_decay_period_type == None,
            ~is_none_or_empty(models.GroundWater.infiltration_decay_period_file),
        ),
        message="an infiltration decay period type (v2_groundwater.infiltration_decay_period_type) should be defined when using an infiltration decay period file.",
    ),
    QueryCheck(
        error_code=409,
        column=models.GroundWater.groundwater_hydro_connectivity_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.groundwater_hydro_connectivity_type == None,
            ~is_none_or_empty(models.GroundWater.groundwater_hydro_connectivity_file),
        ),
        message="a groundwater hydro connectivity type (v2_groundwater.groundwater_hydro_connectivity_type) should be defined when using a groundwater hydro connectivity file.",
    ),
    QueryCheck(
        error_code=410,
        column=models.GroundWater.groundwater_impervious_layer_level,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.groundwater_impervious_layer_level == None,
            is_none_or_empty(
                models.GroundWater.groundwater_impervious_layer_level_file
            ),
        ),
        message="a global impervious layer level (v2_groundwater.groundwater_impervious_layer_level) should be defined when not using an impervious layer level file",
    ),
    QueryCheck(
        error_code=411,
        column=models.GroundWater.groundwater_impervious_layer_level_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.groundwater_impervious_layer_level_type == None,
            ~is_none_or_empty(
                models.GroundWater.groundwater_impervious_layer_level_file
            ),
        ),
        message="a impervious layer level type (v2_groundwater.groundwater_impervious_layer_level_type) should be defined when using an impervious layer level file",
    ),
    QueryCheck(
        error_code=412,
        column=models.GroundWater.initial_infiltration_rate,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.initial_infiltration_rate == None,
            is_none_or_empty(models.GroundWater.initial_infiltration_rate_file),
        ),
        message="a global initial infiltration rate (v2_groundwater.initial_infiltration_rate) should be defined when not using an initial infiltration rate file.",
    ),
    QueryCheck(
        error_code=413,
        column=models.GroundWater.initial_infiltration_rate_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.initial_infiltration_rate_type == None,
            ~is_none_or_empty(models.GroundWater.initial_infiltration_rate_file),
        ),
        message="a initial infiltration rate type (v2_groundwater.initial_infiltration_rate_type) should be defined when using an initial infiltration rate file.",
    ),
    QueryCheck(
        error_code=414,
        column=models.GroundWater.phreatic_storage_capacity,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.phreatic_storage_capacity == None,
            is_none_or_empty(models.GroundWater.phreatic_storage_capacity_file),
        ),
        message="a global phreatic storage capacity (v2_groundwater.phreatic_storage_capacity) should be defined when using a phreatic storage capacity file.",
    ),
    QueryCheck(
        error_code=415,
        column=models.GroundWater.phreatic_storage_capacity_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.global_settings != None,
            models.GroundWater.phreatic_storage_capacity_type == None,
            ~is_none_or_empty(models.GroundWater.phreatic_storage_capacity_file),
        ),
        message="a phreatic storage capacity type (v2_groundwater.phreatic_storage_capacity_type) should be defined when using a phreatic storage capacity file.",
    ),
    QueryCheck(
        error_code=416,
        column=models.Interflow.porosity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            models.Interflow.porosity == None,
            is_none_or_empty(models.Interflow.porosity_file),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="a global porosity (v2_interflow.porosity) should be defined when not using a porosity file.",
    ),
    QueryCheck(
        error_code=417,
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
        message=f"a porosity layer thickness (v2_interflow.porosity_layer_thickness) should be defined and >0 when "
        f"interflow_type is "
        f"{constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY} or "
        f"{constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY}",
    ),
    QueryCheck(
        error_code=418,
        column=models.Interflow.impervious_layer_elevation,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            models.Interflow.impervious_layer_elevation == None,
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message=f"the impervious layer elevation (v2_interflow.impervious_layer_elevation) cannot be null when "
        f"v2_interflow.interflow_type is not {constants.InterflowType.NO_INTERLFOW}",
    ),
    QueryCheck(
        error_code=419,
        column=models.Interflow.hydraulic_conductivity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.global_settings != None,
            models.Interflow.hydraulic_conductivity == None,
            is_none_or_empty(models.Interflow.hydraulic_conductivity_file),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="v2_interflow.hydraulic_conductivity cannot be null when no hydraulic conductivity file is supplied.",
    ),
    RangeCheck(
        error_code=420,
        column=models.GroundWater.phreatic_storage_capacity,
        filters=models.GroundWater.global_settings != None,
        min_value=0,
        max_value=1,
    ),
]


## 06xx: INFLOW
_0d_surf = models.GlobalSetting.use_0d_inflow == constants.InflowType.SURFACE
_0d_imp = models.GlobalSetting.use_0d_inflow == constants.InflowType.IMPERVIOUS_SURFACE

for (surface, surface_map, _filters) in [
    (models.Surface, models.SurfaceMap, _0d_surf),
    (models.ImperviousSurface, models.ImperviousSurfaceMap, _0d_imp),
]:
    CHECKS += [
        RangeCheck(
            error_code=601,
            column=getattr(surface, "area"),
            min_value=0,
            filters=_filters,
        ),
        RangeCheck(
            level=CheckLevel.WARNING,
            error_code=602,
            column=getattr(surface, "dry_weather_flow"),
            min_value=0,
            filters=_filters,
        ),
        RangeCheck(
            error_code=603,
            column=getattr(surface_map, "percentage"),
            min_value=0,
            filters=_filters,
        ),
        RangeCheck(
            error_code=604,
            level=CheckLevel.WARNING,
            column=getattr(surface_map, "percentage"),
            max_value=100,
            filters=_filters,
        ),
        RangeCheck(
            error_code=605,
            column=getattr(surface, "nr_of_inhabitants"),
            min_value=0,
            filters=_filters,
        ),
    ]

CHECKS += [
    RangeCheck(
        error_code=606,
        column=models.SurfaceParameter.outflow_delay,
        min_value=0,
        filters=_0d_surf,
    ),
    RangeCheck(
        error_code=607,
        column=models.SurfaceParameter.max_infiltration_capacity,
        min_value=0,
        filters=_0d_surf,
    ),
    RangeCheck(
        error_code=608,
        column=models.SurfaceParameter.min_infiltration_capacity,
        min_value=0,
        filters=_0d_surf,
    ),
    RangeCheck(
        error_code=609,
        column=models.SurfaceParameter.infiltration_decay_constant,
        min_value=0,
        filters=_0d_surf,
    ),
    RangeCheck(
        error_code=610,
        column=models.SurfaceParameter.infiltration_recovery_constant,
        min_value=0,
        filters=_0d_surf,
    ),
    Use0DFlowCheck(error_code=611),
]


# 07xx: FILE EXISTENCE
CHECKS += [
    FileExistsCheck(error_code=701, column=models.GlobalSetting.dem_file),
    FileExistsCheck(error_code=702, column=models.GlobalSetting.frict_coef_file),
    FileExistsCheck(error_code=703, column=models.GlobalSetting.interception_file),
    FileExistsCheck(
        error_code=704,
        column=models.Interflow.porosity_file,
        filters=models.Interflow.global_settings != None,
    ),
    FileExistsCheck(
        error_code=705,
        column=models.Interflow.hydraulic_conductivity_file,
        filters=models.Interflow.global_settings != None,
    ),
    FileExistsCheck(
        error_code=706,
        column=models.SimpleInfiltration.infiltration_rate_file,
        filters=models.SimpleInfiltration.global_settings != None,
    ),
    FileExistsCheck(
        error_code=707,
        column=models.SimpleInfiltration.max_infiltration_capacity_file,
        filters=models.SimpleInfiltration.global_settings != None,
    ),
    FileExistsCheck(
        error_code=708,
        column=models.GroundWater.groundwater_impervious_layer_level_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        error_code=709,
        column=models.GroundWater.phreatic_storage_capacity_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        error_code=710,
        column=models.GroundWater.equilibrium_infiltration_rate_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        error_code=711,
        column=models.GroundWater.initial_infiltration_rate_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        error_code=712,
        column=models.GroundWater.infiltration_decay_period_file,
        filters=models.GroundWater.global_settings != None,
    ),
    FileExistsCheck(
        error_code=713,
        column=models.GroundWater.groundwater_hydro_connectivity_file,
        filters=models.GroundWater.global_settings != None,
    ),
]


## 11xx: SIMULATION SETTINGS

CHECKS += [
    GeneralCheck(
        error_code=1101,
        column=models.GlobalSetting.maximum_sim_time_step,
        criterion_valid=models.GlobalSetting.maximum_sim_time_step
        >= models.GlobalSetting.sim_time_step,
    ),
    GeneralCheck(
        error_code=1102,
        column=models.GlobalSetting.sim_time_step,
        criterion_valid=models.GlobalSetting.sim_time_step
        >= models.GlobalSetting.minimum_sim_time_step,
    ),
    QueryCheck(
        error_code=1103,
        column=models.GlobalSetting.maximum_sim_time_step,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.timestep_plus == True,
            models.GlobalSetting.maximum_sim_time_step == None,
        ),
        message="v2_global_settings.maximum_sim_time_step cannot be null when "
        "v2_global_settings.timestep_plus is True",
    ),
    RangeCheck(
        error_code=1104,
        column=models.NumericalSettings.convergence_eps,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=1105,
        column=models.NumericalSettings.convergence_cg,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=1106,
        column=models.NumericalSettings.general_numerical_threshold,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=1107,
        column=models.NumericalSettings.flow_direction_threshold,
        min_value=0,
        left_inclusive=False,
    ),
]
CHECKS += [
    TimeseriesCheck(col, error_code=1108)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
        models.Lateral1d.timeseries,
        models.Lateral2D.timeseries,
    ]
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
        self.checks = []
        # Error codes 1 to 9: factories
        for model in self.models:
            self.checks += generate_foreign_key_checks(model.__table__, error_code=1)
            self.checks += generate_unique_checks(model.__table__, error_code=2)
            self.checks += generate_not_null_checks(model.__table__, error_code=3)
            self.checks += generate_type_checks(model.__table__, error_code=4)
            self.checks += generate_geometry_checks(model.__table__, error_code=5)
            self.checks += generate_geometry_type_checks(model.__table__, error_code=6)
            self.checks += generate_enum_checks(
                model.__table__,
                error_code=7,
                custom_level_map={
                    "sewerage_type": "INFO",
                    "zoom_category": "INFO",
                    "material": "INFO",
                },
            )

        self.checks += CHECKS

    def iter_checks(self, level=CheckLevel.ERROR):
        """Iterate over checks with at least 'level'"""
        level = CheckLevel.get(level)  # normalize
        for check in self.checks:
            if check.level >= level:
                yield check
