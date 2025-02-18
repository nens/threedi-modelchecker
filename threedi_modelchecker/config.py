from typing import List

from geoalchemy2 import functions as geo_func
from sqlalchemy import and_, func, or_, true
from sqlalchemy.orm import Query
from threedi_schema import constants, models
from threedi_schema.beta_features import BETA_COLUMNS, BETA_VALUES

from .checks.base import (
    AllEqualCheck,
    BaseCheck,
    CheckLevel,
    ListOfIntsCheck,
    NotNullCheck,
    QueryCheck,
    RangeCheck,
    UniqueCheck,
)
from .checks.cross_section_definitions import (
    CrossSectionExpectEmptyCheck,
    CrossSectionFirstElementNonZeroCheck,
    CrossSectionFirstElementZeroCheck,
    CrossSectionFrictionCorrectLengthCheck,
    CrossSectionGreaterZeroCheck,
    CrossSectionIncreasingCheck,
    CrossSectionListCheck,
    CrossSectionMinimumDiameterCheck,
    CrossSectionNullCheck,
    CrossSectionTableCheck,
    CrossSectionVariableFrictionRangeCheck,
    CrossSectionVegetationCorrectLengthCheck,
    CrossSectionVegetationTableNotNegativeCheck,
    CrossSectionYZCoordinateCountCheck,
    CrossSectionYZHeightCheck,
    CrossSectionYZIncreasingWidthIfOpenCheck,
)
from .checks.factories import (
    ForeignKeyCheckSetting,
    generate_enum_checks,
    generate_epsg_geom_checks,
    generate_epsg_raster_checks,
    generate_foreign_key_checks,
    generate_geometry_checks,
    generate_geometry_type_checks,
    generate_not_null_checks,
    generate_type_checks,
    generate_unique_checks,
)
from .checks.location import (
    ConnectionNodeLinestringLocationCheck,
    DWFMapLinestringLocationCheck,
    MeasureMapLinestringMapLocationCheck,
    PointLocationCheck,
    PumpMapLinestringLocationCheck,
    SurfaceMapLinestringLocationCheck,
)
from .checks.other import (
    AllPresentVegetationParameters,
    BetaColumnsCheck,
    BetaValuesCheck,
    BoundaryCondition1DObjectNumberCheck,
    ChannelManholeLevelCheck,
    ConnectionNodesDistance,
    ConnectionNodesLength,
    ControlHasSingleMeasureVariable,
    CorrectAggregationSettingsExist,
    CrossSectionSameConfigurationCheck,
    DefinedAreaCheck,
    DWFDistributionCSVFormatCheck,
    DWFDistributionLengthCheck,
    DWFDistributionSumCheck,
    FeatureClosedCrossSectionCheck,
    InflowNoFeaturesCheck,
    MaxOneRecordCheck,
    NodeSurfaceConnectionsCheck,
    OpenChannelsWithNestedNewton,
    PotentialBreachInterdistanceCheck,
    PotentialBreachStartEndCheck,
    PumpStorageTimestepCheck,
    SpatialIndexCheck,
    SurfaceNodeInflowAreaCheck,
    TagsValidCheck,
    Use0DFlowCheck,
    UsedSettingsPresentCheck,
    UsedSettingsPresentCheckSingleTable,
)
from .checks.raster import (
    GDALAvailableCheck,
    RasterCompressionUsedCheck,
    RasterExistsCheck,
    RasterGridSizeCheck,
    RasterHasOneBandCheck,
    RasterIsValidCheck,
    RasterPixelCountCheck,
    RasterRangeCheck,
    RasterSquareCellsCheck,
)
from .checks.timeseries import (
    FirstTimeSeriesEqualTimestepsCheck,
    TimeSeriesEqualTimestepsCheck,
    TimeseriesExistenceCheck,
    TimeseriesIncreasingCheck,
    TimeseriesRowCheck,
    TimeseriesStartsAtZeroCheck,
    TimeseriesTimestepCheck,
    TimeseriesValueCheck,
)

TOLERANCE_M = 1.0


def is_none_or_empty(col):
    return (col == None) | (col == "")


CONDITIONS = {
    "has_dem": Query(models.ModelSettings).filter(
        ~is_none_or_empty(models.ModelSettings.dem_file)
    ),
    "has_no_dem": Query(models.ModelSettings).filter(
        is_none_or_empty(models.ModelSettings.dem_file)
    ),
    "has_inflow": Query(models.SimulationTemplateSettings).filter(
        models.SimulationTemplateSettings.use_0d_inflow
        != constants.InflowType.NO_INFLOW,
    ),
    "0d_surf": Query(models.SimulationTemplateSettings).filter(
        models.SimulationTemplateSettings.use_0d_inflow == constants.InflowType.SURFACE,
    ),
    "0d_imp": Query(models.SimulationTemplateSettings).filter(
        models.SimulationTemplateSettings.use_0d_inflow
        == constants.InflowType.IMPERVIOUS_SURFACE,
    ),
    "manning": Query(models.ModelSettings).filter(
        models.ModelSettings.friction_type == constants.FrictionType.MANNING,
    ),
    "chezy": Query(models.ModelSettings).filter(
        models.ModelSettings.friction_type == constants.FrictionType.CHEZY,
    ),
    "has_groundwater_flow": Query(models.GroundWater).filter(
        models.GroundWater.groundwater_hydraulic_conductivity.isnot(None)
        | ~is_none_or_empty(models.GroundWater.groundwater_hydraulic_conductivity_file),
    ),
}

nr_grid_levels = Query(models.ModelSettings.nr_grid_levels).scalar_subquery()

cross_section_tables = [
    models.CrossSectionLocation,
    models.Culvert,
    models.Orifice,
    models.Pipe,
    models.Weir,
]

CHECKS: List[BaseCheck] = []

## 002x: FRICTION
CHECKS += [
    QueryCheck(
        error_code=20,
        column=models.CrossSectionLocation.friction_value,
        invalid=(
            Query(models.CrossSectionLocation)
            .filter(
                models.CrossSectionLocation.cross_section_shape
                != constants.CrossSectionShape.TABULATED_YZ
            )
            .filter(models.CrossSectionLocation.friction_value == None)
        ),
        message="CrossSectionLocation.friction_value cannot be null or empty",
    )
]
CHECKS += [
    RangeCheck(
        error_code=21,
        column=table.friction_value,
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
        column=table.friction_value,
        filters=(table.crest_type == constants.CrestType.BROAD_CRESTED.value),
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
        level=CheckLevel.WARNING,
        column=table.friction_value,
        filters=table.friction_type == constants.FrictionType.MANNING.value,
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
        message=f"{table.__tablename__}.friction_value is not less than 1 while MANNING friction is selected. CHEZY friction will be used instead. In the future this will lead to an error.",
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
        level=CheckLevel.WARNING,
        column=table.friction_value,
        filters=(table.friction_type == constants.FrictionType.MANNING.value)
        & (table.crest_type == constants.CrestType.BROAD_CRESTED.value),
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
        message=f"{table.__tablename__}.friction_value is not less than 1 while MANNING friction is selected. CHEZY friction will be used instead. In the future this will lead to an error.",
    )
    for table in [
        models.Orifice,
        models.Weir,
    ]
]
CHECKS += [
    NotNullCheck(
        error_code=24,
        column=table.friction_value,
        filters=(
            (table.crest_type == constants.CrestType.BROAD_CRESTED.value)
            & ((table.material_id.is_(None)) | (table.friction_type.isnot(None)))
        ),
    )
    for table in [models.Orifice, models.Weir]
]
CHECKS += [
    NotNullCheck(
        error_code=24,
        column=table.friction_value,
        filters=((table.material_id.is_(None)) | (table.friction_type.isnot(None))),
    )
    for table in [models.Culvert, models.Pipe]
]
CHECKS += [
    NotNullCheck(
        error_code=25,
        column=table.friction_type,
        filters=(
            (table.crest_type == constants.CrestType.BROAD_CRESTED.value)
            & ((table.material_id.is_(None)) | (table.friction_value.isnot(None)))
        ),
    )
    for table in [models.Orifice, models.Weir]
]
CHECKS += [
    NotNullCheck(
        error_code=25,
        column=table.friction_type,
        filters=((table.material_id.is_(None)) | (table.friction_value.isnot(None))),
    )
    for table in [models.Culvert, models.Pipe]
]


# Friction with conveyance should raise an error when used
# on a column other than models.CrossSectionLocation

CHECKS += [
    QueryCheck(
        error_code=26,
        column=table.friction_type,
        invalid=Query(table)
        .outerjoin(models.Material, table.material_id == models.Material.id)
        .filter(
            or_(
                table.friction_type.in_(
                    [
                        constants.FrictionType.CHEZY_CONVEYANCE,
                        constants.FrictionType.MANNING_CONVEYANCE,
                    ]
                ),
                and_(
                    table.friction_type == None,
                    models.Material.friction_type.in_(
                        [
                            constants.FrictionType.CHEZY_CONVEYANCE,
                            constants.FrictionType.MANNING_CONVEYANCE,
                        ]
                    ),
                ),
            )
        ),
        message=(
            "Friction with conveyance, such as chezy_conveyance and "
            "manning_conveyance, may only be used with cross_section_location"
        ),
    )
    for table in [models.Pipe, models.Culvert, models.Weir, models.Orifice]
]


# Friction with conveyance should only be used on
# tabulated rectangle, tabulated trapezium, or tabulated yz shapes
CHECKS += [
    QueryCheck(
        error_code=27,
        column=models.CrossSectionLocation.id,
        invalid=Query(models.CrossSectionLocation).filter(
            (
                models.CrossSectionLocation.cross_section_shape.not_in(
                    [
                        constants.CrossSectionShape.TABULATED_RECTANGLE,
                        constants.CrossSectionShape.TABULATED_TRAPEZIUM,
                        constants.CrossSectionShape.TABULATED_YZ,
                    ]
                )
            )
            & (
                models.CrossSectionLocation.friction_type.in_(
                    [
                        constants.FrictionType.CHEZY_CONVEYANCE,
                        constants.FrictionType.MANNING_CONVEYANCE,
                    ]
                )
            )
        ),
        message=(
            "in cross_section_location, friction with "
            "conveyance, such as chezy_conveyance and "
            "manning_conveyance, may only be used with "
            "tabulated rectangle (5), tabulated trapezium (6), "
            "or tabulated yz (7) shapes"
        ),
    )
]


## 003x: CALCULATION TYPE

CHECKS += [
    QueryCheck(
        error_code=31,
        column=models.Channel.exchange_type,
        filters=CONDITIONS["has_no_dem"].exists(),
        invalid=Query(models.Channel).filter(
            models.Channel.exchange_type.in_(
                [
                    constants.CalculationType.EMBEDDED,
                    constants.CalculationType.CONNECTED,
                    constants.CalculationType.DOUBLE_CONNECTED,
                ]
            ),
        ),
        message=f"channel.exchange_type cannot be "
        f"{constants.CalculationType.EMBEDDED}, "
        f"{constants.CalculationType.CONNECTED} or "
        f"{constants.CalculationType.DOUBLE_CONNECTED} when "
        f"model_settings.dem_file is null",
    )
]

## 004x: VARIOUS OBJECT SETTINGS
CHECKS += [
    RangeCheck(
        error_code=41,
        column=table.discharge_coefficient_negative,
        min_value=0,
    )
    for table in [models.Culvert, models.Weir, models.Orifice]
]
CHECKS += [
    RangeCheck(
        error_code=42,
        column=table.discharge_coefficient_positive,
        min_value=0,
    )
    for table in [models.Culvert, models.Weir, models.Orifice]
]
CHECKS += [
    RangeCheck(
        error_code=43,
        level=CheckLevel.WARNING,
        column=table.calculation_point_distance,
        min_value=0,
        left_inclusive=False,  # 0 itself is not allowed
        message=f"{table.__tablename__}.calculation_point_distance is not greater than 0, in the future this will lead to an error",
    )
    for table in [models.Channel, models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        error_code=44,
        column=models.ConnectionNode.storage_area,
        invalid=Query(models.ConnectionNode).filter(
            models.ConnectionNode.visualisation != None,
            models.ConnectionNode.storage_area < 0,
        ),
        message="connection_node.storage_area for manhole connection node should greater than or equal to 0",
    ),
]
CHECKS += [
    RangeCheck(
        error_code=44,
        level=CheckLevel.WARNING,
        column=table.calculation_point_distance,
        min_value=5,
        left_inclusive=True,
        message=f"{table.__tablename__}.calculation_point_distance should preferably be at least 5.0 metres to prevent simulation timestep reduction.",
    )
    for table in [models.Channel, models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        error_code=45,
        level=CheckLevel.FUTURE_ERROR,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(
            or_(
                models.ConnectionNode.storage_area.is_(None),
                models.ConnectionNode.storage_area < 0,
            )
        )
        .filter(
            models.ConnectionNode.id.notin_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Channel.connection_node_id_start),
                    Query(models.Channel.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                    Query(models.Weir.connection_node_id_start),
                    Query(models.Weir.connection_node_id_end),
                    Query(models.Orifice.connection_node_id_start),
                    Query(models.Orifice.connection_node_id_end),
                )
            ),
        ),
        message="connection_node.storage_area should be defined and greater than 0 if the connection nodes "
        "has no connections to channels, culverts, pipes, weirs, or orifices0. "
        "From September 2025 onwards, this will be an ERROR.",
    )
]

CHECKS += [
    QueryCheck(
        error_code=46,
        level=CheckLevel.FUTURE_ERROR,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(models.ConnectionNode.bottom_level.is_(None))
        .filter(
            models.ConnectionNode.id.notin_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Channel.connection_node_id_start),
                    Query(models.Channel.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                    Query(models.Weir.connection_node_id_start),
                    Query(models.Weir.connection_node_id_end),
                    Query(models.Orifice.connection_node_id_start),
                    Query(models.Orifice.connection_node_id_end),
                )
            ),
        ),
        message="A connection node that is not connected to a pipe, "
        "channel, culvert, weir, or orifice must have a defined bottom_level.",
    ),
]
CHECKS += [
    QueryCheck(
        error_code=47,
        level=CheckLevel.FUTURE_ERROR,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(
            models.ConnectionNode.exchange_type.in_(
                [
                    constants.CalculationTypeNode.CONNECTED,
                    constants.CalculationTypeNode.ISOLATED,
                ]
            )
        )
        .filter(
            or_(
                models.ConnectionNode.storage_area.is_(None),
                models.ConnectionNode.storage_area < 0,
            )
        )
        .filter(
            models.ConnectionNode.id.notin_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Channel.connection_node_id_start),
                    Query(models.Channel.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                )
            ),
        )
        .filter(
            models.ConnectionNode.id.in_(
                Query(models.Weir.connection_node_id_start).union_all(
                    Query(models.Weir.connection_node_id_end),
                    Query(models.Orifice.connection_node_id_start),
                    Query(models.Orifice.connection_node_id_end),
                )
            ),
        ),
        message=(
            "connection_node.storage_area for a node that is connected to a weir or an orifice, "
            "and that has exchange type CONNECTED or ISOLATED should be defined and greater than 0. "
            "From September 2025 onwards, this will be an ERROR."
        ),
    )
]

CHECKS += [
    QueryCheck(
        error_code=48,
        level=CheckLevel.ERROR,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(
            models.ConnectionNode.exchange_type.in_(
                [
                    constants.CalculationTypeNode.CONNECTED,
                    constants.CalculationTypeNode.ISOLATED,
                ]
            )
        )
        .filter(models.ConnectionNode.bottom_level.is_(None))
        .filter(
            models.ConnectionNode.id.notin_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Channel.connection_node_id_start),
                    Query(models.Channel.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                )
            ),
        )
        .filter(
            models.ConnectionNode.id.in_(
                Query(models.Weir.connection_node_id_start).union_all(
                    Query(models.Weir.connection_node_id_end),
                    Query(models.Orifice.connection_node_id_start),
                    Query(models.Orifice.connection_node_id_end),
                )
            ),
        ),
        message=(
            "connection_node.bottom_level for a node that is connected to a weir or an orifice, "
            "and that has exchange type CONNECTED or ISOLATED should be defined"
        ),
    )
]

CHECKS += [
    QueryCheck(
        error_code=49,
        level=CheckLevel.WARNING,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(models.ConnectionNode.bottom_level.is_(None))
        .filter(
            models.ConnectionNode.id.not_in(
                Query(models.Channel.connection_node_id_start).union_all(
                    Query(models.Channel.connection_node_id_end)
                ),
            )
        )
        .filter(
            models.ConnectionNode.id.in_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                )
            ),
        ),
        message=(
            "connection_node.bottom_level for a node that is connected to a pipe or a culvert, "
            "and that is not connected to a channel should be defined. "
            "In the future, this will lead to an error."
        ),
    )
]

CHECKS += [
    QueryCheck(
        error_code=50,
        level=CheckLevel.WARNING,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(
            or_(
                models.ConnectionNode.storage_area.is_(None),
                models.ConnectionNode.storage_area < 0,
            )
        )
        .filter(
            models.ConnectionNode.id.not_in(
                Query(models.Channel.connection_node_id_start).union_all(
                    Query(models.Channel.connection_node_id_end)
                ),
            )
        )
        .filter(
            models.ConnectionNode.id.in_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                )
            ),
        ),
        message=(
            "connection_node.storage_area for a node that is connected to a pipe or a culvert, "
            "and that is not connected to a channel should be defined and greater than 0"
            "In the future, this will lead to an error."
        ),
    )
]

## 005x: CROSS SECTIONS

CHECKS += [
    OpenChannelsWithNestedNewton(error_code=53, column=table.id)
    for table in cross_section_tables
]

CHECKS += [
    QueryCheck(
        error_code=54,
        level=CheckLevel.WARNING,
        column=models.CrossSectionLocation.reference_level,
        invalid=Query(models.CrossSectionLocation).filter(
            models.CrossSectionLocation.reference_level
            > models.CrossSectionLocation.bank_level,
        ),
        message="cross_section_location.bank_level will be ignored if it is below the reference_level",
    ),
    QueryCheck(
        error_code=55,
        column=models.Channel.id,
        invalid=Query(models.Channel)
        .outerjoin(
            models.CrossSectionLocation,
            models.Channel.id == models.CrossSectionLocation.channel_id,
        )
        .filter(models.CrossSectionLocation.channel_id == None),
        message="channel has no cross section locations",
    ),
    CrossSectionSameConfigurationCheck(
        error_code=56,
        level=CheckLevel.ERROR,
        column=models.Channel.id,
    ),
]

CHECKS += [
    FeatureClosedCrossSectionCheck(
        error_code=57, level=CheckLevel.INFO, column=table.id
    )
    for table in [models.Pipe, models.Culvert]
]

## 006x: PUMPSTATIONS
CHECKS += [
    QueryCheck(
        error_code=61,
        column=models.Pump.upper_stop_level,
        invalid=Query(models.Pump).filter(
            models.Pump.upper_stop_level <= models.Pump.start_level,
        ),
        message="pump.upper_stop_level should be greater than pump.start_level",
    ),
    QueryCheck(
        error_code=62,
        column=models.Pump.lower_stop_level,
        invalid=Query(models.Pump).filter(
            models.Pump.lower_stop_level >= models.Pump.start_level,
        ),
        message="pump.lower_stop_level should be less than pump.start_level",
    ),
    QueryCheck(
        error_code=63,
        level=CheckLevel.WARNING,
        column=models.ConnectionNode.storage_area,
        invalid=Query(models.ConnectionNode, models.Pump)
        .join(
            models.PumpMap,
            models.PumpMap.connection_node_id_end == models.ConnectionNode.id,
        )
        .join(models.Pump, models.PumpMap.pump_id == models.Pump.id)
        .filter(models.ConnectionNode.storage_area != None)
        .filter(models.ConnectionNode.storage_area * 1000 <= models.Pump.capacity),
        message=(
            "connection_node.storage_area * 1000 for each pump's end connection node must be greater than pump.capacity; "
            + "water level should not rise >= 1 m in one second"
        ),
    ),
    RangeCheck(
        error_code=64,
        column=models.Pump.capacity,
        min_value=0,
    ),
    QueryCheck(
        error_code=65,
        level=CheckLevel.WARNING,
        column=models.Pump.capacity,
        invalid=Query(models.Pump).filter(models.Pump.capacity == 0.0),
        message="pump.capacity should be be greater than 0",
    ),
    PumpStorageTimestepCheck(
        error_code=66,
        level=CheckLevel.WARNING,
        column=models.Pump.capacity,
    ),
]

## 007x: BOUNDARY CONDITIONS
CHECKS += [
    QueryCheck(
        error_code=71,
        column=models.BoundaryCondition1D.connection_node_id,
        level=CheckLevel.FUTURE_ERROR,
        invalid=Query(models.BoundaryCondition1D).filter(
            models.BoundaryCondition1D.connection_node_id
            == models.Pump.connection_node_id
            | models.BoundaryCondition1D.connection_node_id
            == models.PumpMap.connection_node_id_end
        ),
        message="boundary_condition_1d cannot be connected to a pump",
    ),
    # 1d boundary conditions should be connected to exactly 1 object
    BoundaryCondition1DObjectNumberCheck(error_code=72),
    QueryCheck(
        error_code=73,
        column=models.BoundaryConditions2D.type,
        filters=~CONDITIONS["has_groundwater_flow"].exists(),
        invalid=Query(models.BoundaryConditions2D).filter(
            models.BoundaryConditions2D.type.in_(
                [
                    constants.BoundaryType.GROUNDWATERLEVEL,
                    constants.BoundaryType.GROUNDWATERDISCHARGE,
                ]
            )
        ),
        message=(
            "boundary_condition_2d cannot have a groundwater type when there "
            "is no groundwater hydraulic conductivity"
        ),
    ),
    QueryCheck(
        error_code=74,
        column=models.BoundaryCondition1D.type,
        invalid=Query(models.BoundaryCondition1D).filter(
            models.BoundaryCondition1D.type.in_(
                [
                    constants.BoundaryType.GROUNDWATERLEVEL,
                    constants.BoundaryType.GROUNDWATERDISCHARGE,
                ]
            )
        ),
        message=("boundary_condition_1d cannot have a groundwater type"),
    ),
]

## 008x: CROSS SECTION DEFINITIONS
CHECKS += [
    QueryCheck(
        error_code=80,
        column=models.CrossSectionLocation.friction_value,
        invalid=(
            Query(models.CrossSectionLocation)
            .filter(
                models.CrossSectionLocation.cross_section_shape
                == constants.CrossSectionShape.TABULATED_YZ
            )
            .filter(models.CrossSectionLocation.friction_value == None)
            .filter(
                (models.CrossSectionLocation.cross_section_friction_values == None)
                | (models.CrossSectionLocation.cross_section_friction_values == "")
            )
        ),
        message=f"Either {models.CrossSectionLocation.friction_value.table.name}.{models.CrossSectionLocation.friction_value.name} "
        f"or {models.CrossSectionLocation.cross_section_friction_values.table.name}.{models.CrossSectionLocation.cross_section_friction_values.name} "
        f" must be defined for a {constants.CrossSectionShape.TABULATED_YZ} cross section shape",
    )
]


for table in cross_section_tables:
    CHECKS += [
        CrossSectionNullCheck(
            error_code=81,
            column=table.cross_section_width,
            shapes=(
                constants.CrossSectionShape.CLOSED_RECTANGLE,
                constants.CrossSectionShape.RECTANGLE,
                constants.CrossSectionShape.CIRCLE,
                constants.CrossSectionShape.EGG,
                constants.CrossSectionShape.INVERTED_EGG,
            ),
        ),
        CrossSectionNullCheck(
            error_code=82,
            column=table.cross_section_height,
            shapes=(constants.CrossSectionShape.CLOSED_RECTANGLE,),
        ),
        CrossSectionNullCheck(
            error_code=83,
            column=table.cross_section_table,
            shapes=(
                constants.CrossSectionShape.TABULATED_RECTANGLE,
                constants.CrossSectionShape.TABULATED_TRAPEZIUM,
                constants.CrossSectionShape.TABULATED_YZ,
            ),
        ),
        CrossSectionGreaterZeroCheck(
            error_code=85,
            column=table.cross_section_width,
            shapes=(
                constants.CrossSectionShape.RECTANGLE,
                constants.CrossSectionShape.CIRCLE,
                constants.CrossSectionShape.CLOSED_RECTANGLE,
                constants.CrossSectionShape.EGG,
                constants.CrossSectionShape.INVERTED_EGG,
            ),
        ),
        CrossSectionGreaterZeroCheck(
            error_code=86,
            column=table.cross_section_height,
            shapes=(constants.CrossSectionShape.CLOSED_RECTANGLE,),
        ),
        CrossSectionTableCheck(
            error_code=87,
            column=table.cross_section_table,
            ncol=2,
            shapes=(
                constants.CrossSectionShape.TABULATED_RECTANGLE,
                constants.CrossSectionShape.TABULATED_TRAPEZIUM,
                constants.CrossSectionShape.TABULATED_YZ,
            ),
        ),
        CrossSectionIncreasingCheck(
            error_code=90,
            column=table.cross_section_table,
            shapes=(
                constants.CrossSectionShape.TABULATED_RECTANGLE,
                constants.CrossSectionShape.TABULATED_TRAPEZIUM,
            ),
        ),
        CrossSectionFirstElementNonZeroCheck(
            error_code=91,
            level=CheckLevel.FUTURE_ERROR,
            column=table.cross_section_table,
            shapes=(constants.CrossSectionShape.TABULATED_RECTANGLE,),
        ),
        CrossSectionFirstElementZeroCheck(
            error_code=92,
            level=CheckLevel.WARNING,
            column=table.cross_section_table,
            shapes=(
                constants.CrossSectionShape.TABULATED_RECTANGLE,
                constants.CrossSectionShape.TABULATED_TRAPEZIUM,
            ),
        ),
        CrossSectionExpectEmptyCheck(
            error_code=94,
            level=CheckLevel.WARNING,
            column=table.cross_section_height,
            shapes=(
                constants.CrossSectionShape.CIRCLE,
                constants.CrossSectionShape.EGG,
                constants.CrossSectionShape.INVERTED_EGG,
            ),
        ),
        CrossSectionMinimumDiameterCheck(
            column=table.id,
            error_code=98,
            level=CheckLevel.WARNING,
            filters=table.cross_section_shape.isnot(None),
        ),
    ]

CHECKS += [
    # Checks for channels (culvert, orfice, pipe and weir cannot have YZ profile)
    CrossSectionYZHeightCheck(
        error_code=95,
        column=models.CrossSectionLocation.cross_section_table,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
    ),
    CrossSectionYZCoordinateCountCheck(
        column=models.CrossSectionLocation.cross_section_table,
        error_code=96,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
    ),
    CrossSectionYZIncreasingWidthIfOpenCheck(
        column=models.CrossSectionLocation.cross_section_table,
        error_code=97,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
    ),
]

CHECKS += [
    CrossSectionListCheck(
        error_code=87,
        column=models.CrossSectionLocation.cross_section_friction_values,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
    )
]

## 01xx: LEVEL CHECKS
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=102,
        column=table.invert_level_start,
        invalid=Query(table)
        .join(
            models.ConnectionNode,
            table.connection_node_id_start == models.ConnectionNode.id,
        )
        .filter(models.ConnectionNode.visualisation != None)
        .filter(
            table.invert_level_start < models.ConnectionNode.bottom_level,
        ),
        message=f"{table.__tablename__}.invert_level_start should be higher than or equal to connection_node.bottom_level. In the future, this will lead to an error.",
    )
    for table in [models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=103,
        column=table.invert_level_end,
        invalid=Query(table)
        .join(
            models.ConnectionNode,
            table.connection_node_id_end == models.ConnectionNode.id,
        )
        .filter(models.ConnectionNode.visualisation != None)
        .filter(
            table.invert_level_end < models.ConnectionNode.bottom_level,
        ),
        message=f"{table.__tablename__}.invert_level_end should be higher than or equal to connection_node.bottom_level. In the future, this will lead to an error.",
    )
    for table in [models.Pipe, models.Culvert]
]
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=104,
        column=models.Pump.lower_stop_level,
        invalid=Query(models.Pump)
        .join(
            models.ConnectionNode,
            models.Pump.connection_node_id == models.ConnectionNode.id,
        )
        .filter(models.ConnectionNode.visualisation != None)
        .filter(
            models.Pump.type_ == constants.PumpType.SUCTION_SIDE,
            models.Pump.lower_stop_level <= models.ConnectionNode.bottom_level,
        ),
        message="pump.lower_stop_level should be higher than "
        "connection_node.bottom_level. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=105,
        column=models.Pump.lower_stop_level,
        invalid=Query(models.Pump)
        .join(
            models.ConnectionNode,
            models.Pump.connection_node_id == models.ConnectionNode.id,
        )
        .filter(models.ConnectionNode.visualisation != None)
        .filter(
            models.Pump.type_ == constants.PumpType.DELIVERY_SIDE,
            models.Pump.lower_stop_level <= models.ConnectionNode.bottom_level,
        ),
        message="pump.lower_stop_level should be higher than "
        "connection_node.bottom_level. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=106,
        column=models.ConnectionNode.bottom_level,
        invalid=Query(models.ConnectionNode)
        .filter(models.ConnectionNode.visualisation != None)
        .filter(
            models.ConnectionNode.exchange_type.in_(
                [constants.CalculationTypeNode.CONNECTED]
            )
        )
        .filter(
            models.ConnectionNode.exchange_level < models.ConnectionNode.bottom_level
        ),
        message="connection_node.exchange_level >= connection_node.bottom_level when "
        "connection_node.exchange_type is CONNECTED. In the future, this will lead to an error.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=107,
        column=models.ConnectionNode.exchange_level,
        filters=CONDITIONS["has_no_dem"]
        .filter(models.ModelSettings.manhole_aboveground_storage_area > 0)
        .exists(),
        invalid=Query(models.ConnectionNode).filter(
            models.ConnectionNode.exchange_type.in_(
                [constants.CalculationTypeNode.CONNECTED]
            ),
            models.ConnectionNode.exchange_level == None,
        ),
        message="connection_node.exchange_level cannot be null when using sub-basins (model_settings.manhole_aboveground_storage_area > 0) and no DEM is supplied.",
    ),
]
CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=108,
        column=table.crest_level,
        invalid=Query(table)
        .join(
            models.ConnectionNode,
            (table.connection_node_id_start == models.ConnectionNode.id)
            | (table.connection_node_id_end == models.ConnectionNode.id),
        )
        .filter(models.ConnectionNode.bottom_level != None)
        .filter(table.crest_level < models.ConnectionNode.bottom_level),
        message=f"{table.__tablename__}.crest_level should be higher than or equal to connection_node.bottom_level for all the connected manholes.",
    )
    for table in [models.Weir, models.Orifice]
]
CHECKS += [
    ChannelManholeLevelCheck(
        level=CheckLevel.INFO, nodes_to_check="start", error_code=109
    ),
    ChannelManholeLevelCheck(
        level=CheckLevel.INFO, nodes_to_check="end", error_code=110
    ),
]


## 020x: Spatial checks

CHECKS += [ConnectionNodesDistance(error_code=201, minimum_distance=0.1)]
CHECKS += [
    QueryCheck(
        error_code=202,
        level=CheckLevel.WARNING,
        column=table.id,
        invalid=Query(table).filter(geo_func.ST_Length(table.geom) < 5),
        message=f"The length of {table.__tablename__} is very short (< 5 m). A length of at least 5.0 m is recommended to avoid timestep reduction.",
    )
    for table in [models.Channel, models.Culvert]
]
CHECKS += [
    ConnectionNodesLength(
        error_code=203,
        level=CheckLevel.WARNING,
        column=models.Pipe.id,
        start_node=models.Pipe.connection_node_id_start,
        end_node=models.Pipe.connection_node_id_end,
        min_distance=5.0,
        recommended_distance=5.0,
    )
]
CHECKS += [
    ConnectionNodesLength(
        error_code=204,
        level=CheckLevel.WARNING,
        column=table.id,
        filters=table.crest_type == constants.CrestType.BROAD_CRESTED,
        start_node=table.connection_node_id_start,
        end_node=table.connection_node_id_end,
        min_distance=5.0,
        recommended_distance=5.0,
    )
    for table in [models.Orifice, models.Weir]
]


CHECKS += [
    ConnectionNodeLinestringLocationCheck(
        error_code=205, column=table.geom, max_distance=1
    )
    for table in [
        models.Channel,
        models.Culvert,
        models.Orifice,
        models.Pipe,
        models.Weir,
    ]
]

CHECKS += [
    MeasureMapLinestringMapLocationCheck(
        control_table=table,
        filters=models.MeasureMap.control_type == control_type,
        max_distance=1,
        error_code=205,
    )
    for table, control_type in [
        (models.TableControl, "table"),
        (models.MemoryControl, "memory"),
    ]
]

CHECKS += [
    check(max_distance=1, error_code=205)
    for check in [
        DWFMapLinestringLocationCheck,
        SurfaceMapLinestringLocationCheck,
        PumpMapLinestringLocationCheck,
    ]
]


CHECKS += [
    PointLocationCheck(
        level=CheckLevel.WARNING,
        max_distance=TOLERANCE_M,
        error_code=206,
        column=models.CrossSectionLocation.geom,
        ref_column=models.CrossSectionLocation.channel_id,
        ref_table=models.Channel,
    ),
    PointLocationCheck(
        max_distance=TOLERANCE_M,
        error_code=206,
        column=models.Windshielding1D.geom,
        ref_column=models.Windshielding1D.channel_id,
        ref_table=models.Channel,
    ),
]

CHECKS += [
    PointLocationCheck(
        level=CheckLevel.WARNING,
        max_distance=TOLERANCE_M,
        error_code=206,
        column=table.geom,
        ref_column=table.connection_node_id,
        ref_table=models.ConnectionNode,
    )
    for table in [
        models.BoundaryCondition1D,
        models.MeasureLocation,
        models.Lateral1D,
        models.Pump,
    ]
]

control_tables = [models.MemoryControl, models.TableControl]
ref_tables = [
    models.Pipe,
    models.Orifice,
    models.Culvert,
    models.Weir,
    models.Pump,
]

CHECKS += [
    PointLocationCheck(
        level=CheckLevel.WARNING,
        max_distance=TOLERANCE_M,
        error_code=206,
        column=table.geom,
        ref_column=table.target_id,
        ref_table=ref_table,
        filters=(table.target_type == ref_table.__tablename__),
    )
    for table in [models.MemoryControl, models.TableControl]
    for ref_table in [
        models.Channel,
        models.Pipe,
        models.Orifice,
        models.Culvert,
        models.Weir,
        models.Pump,
    ]
]


CHECKS += [
    SpatialIndexCheck(
        error_code=207, column=models.ConnectionNode.geom, level=CheckLevel.WARNING
    )
]
CHECKS += [
    DefinedAreaCheck(
        error_code=208, column=models.Surface.area, level=CheckLevel.WARNING
    )
]


## 025x: Connectivity

CHECKS += [
    QueryCheck(
        error_code=251,
        level=CheckLevel.WARNING,
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode)
        .filter(models.ConnectionNode.bottom_level != None)
        .filter(
            models.ConnectionNode.exchange_type
            == constants.CalculationTypeNode.ISOLATED,
            models.ConnectionNode.id.notin_(
                Query(models.Pipe.connection_node_id_start).union_all(
                    Query(models.Pipe.connection_node_id_end),
                    Query(models.Channel.connection_node_id_start),
                    Query(models.Channel.connection_node_id_end),
                    Query(models.Culvert.connection_node_id_start),
                    Query(models.Culvert.connection_node_id_end),
                    Query(models.Weir.connection_node_id_start),
                    Query(models.Weir.connection_node_id_end),
                    Query(models.Pump.connection_node_id),
                    Query(models.PumpMap.connection_node_id_end),
                    Query(models.Orifice.connection_node_id_start),
                    Query(models.Orifice.connection_node_id_end),
                )
            ),
        ),
        message="This connection node is not connected to a pipe, channel, culvert, weir, orifice or pumpstation.",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=252,
        column=models.Pipe.id,
        invalid=Query(models.Pipe)
        .join(
            models.ConnectionNode,
            models.Pipe.connection_node_id_start == models.ConnectionNode.id,
        )
        .filter(
            models.Pipe.exchange_type == constants.PipeCalculationType.ISOLATED,
            models.ConnectionNode.storage_area.is_(None),
        )
        .union(
            Query(models.Pipe)
            .join(
                models.ConnectionNode,
                models.Pipe.connection_node_id_end == models.ConnectionNode.id,
            )
            .filter(
                models.Pipe.exchange_type == constants.PipeCalculationType.ISOLATED,
                models.ConnectionNode.storage_area.is_(None),
            )
        ),
        message="When connecting two isolated pipes, it is recommended to add storage to the connection node.",
    ),
]
CHECKS += [
    QueryCheck(
        error_code=253,
        level=CheckLevel.FUTURE_ERROR,
        column=table.connection_node_id_end,
        invalid=Query(table).filter(
            table.connection_node_id_start == table.connection_node_id_end
        ),
        message=f"a {table.__tablename__} cannot be connected to itself (connection_node_id_start must not equal connection_node_id_end)",
    )
    for table in (
        models.Channel,
        models.Culvert,
        models.Orifice,
        models.Pipe,
        models.Weir,
    )
]
CHECKS += [
    QueryCheck(
        error_code=253,
        column=models.Pump.connection_node_id,
        level=CheckLevel.FUTURE_ERROR,
        invalid=(
            Query(models.Pump)
            .join(models.PumpMap, models.PumpMap.id == models.Pump.id)
            .filter(
                models.PumpMap.connection_node_id_end == models.Pump.connection_node_id
            )
        ),
        message="a pump cannot be connected to itself (pump.connection_node_id must not equal the corresponding pump_map.connection_node_id_end)",
    )
]
CHECKS += [
    QueryCheck(
        error_code=255,
        column=models.Pump.connection_node_id,
        invalid=Query(models.Pump)
        .join(models.PumpMap, models.PumpMap.pump_id == models.Pump.id)
        .filter(
            models.Pump.connection_node_id == models.PumpMap.connection_node_id_end
        ),
        message="a pump cannot be connected to itself (pump.connection_node_id must not equal pumpmap.connection_node_id_end)",
    )
]


## 026x: Exchange lines
CHECKS += [
    QueryCheck(
        error_code=260,
        level=CheckLevel.ERROR,
        column=models.Channel.id,
        invalid=Query(models.Channel)
        .join(models.ExchangeLine, models.Channel.id == models.ExchangeLine.channel_id)
        .filter(
            models.Channel.exchange_type.notin_(
                {
                    constants.CalculationType.CONNECTED,
                    constants.CalculationType.DOUBLE_CONNECTED,
                }
            )
        ),
        message="channel can only have an exchange_line if it has "
        "a (double) connected (102 or 105) calculation type",
    ),
    QueryCheck(
        error_code=261,
        level=CheckLevel.ERROR,
        column=models.Channel.id,
        invalid=Query(models.Channel)
        .join(models.ExchangeLine, models.Channel.id == models.ExchangeLine.channel_id)
        .filter(
            models.Channel.exchange_type == constants.CalculationType.CONNECTED,
        )
        .group_by(models.ExchangeLine.channel_id)
        .having(func.count(models.ExchangeLine.id) > 1),
        message="channel can have max 1 exchange_line if it has "
        "connected (102) calculation type",
    ),
    QueryCheck(
        error_code=262,
        level=CheckLevel.ERROR,
        column=models.Channel.id,
        invalid=Query(models.Channel)
        .join(models.ExchangeLine, models.Channel.id == models.ExchangeLine.channel_id)
        .filter(
            models.Channel.exchange_type == constants.CalculationType.DOUBLE_CONNECTED,
        )
        .group_by(models.ExchangeLine.channel_id)
        .having(func.count(models.ExchangeLine.id) > 2),
        message="channel can have max 2 exchange_line if it has "
        "double connected (105) calculation type",
    ),
    QueryCheck(
        error_code=263,
        level=CheckLevel.WARNING,
        column=models.ExchangeLine.geom,
        invalid=Query(models.ExchangeLine)
        .join(models.Channel, models.Channel.id == models.ExchangeLine.channel_id)
        .filter(
            geo_func.ST_Length(models.ExchangeLine.geom)
            < (0.8 * geo_func.ST_Length(models.Channel.geom))
        ),
        message=(
            "exchange_line.geom should not be significantly shorter than its "
            "corresponding channel."
        ),
    ),
    QueryCheck(
        error_code=264,
        level=CheckLevel.WARNING,
        column=models.ExchangeLine.geom,
        invalid=Query(models.ExchangeLine)
        .join(models.Channel, models.Channel.id == models.ExchangeLine.channel_id)
        .filter(
            geo_func.ST_Distance(models.ExchangeLine.geom, models.Channel.geom) > 500.0
        ),
        message=("exchange_line.geom is far (> 500 m) from its corresponding channel"),
    ),
    RangeCheck(
        error_code=265,
        column=models.ExchangeLine.exchange_level,
        min_value=-9998.0,
        max_value=8848.0,
    ),
]

## 027x: Potential breaches
CHECKS += [
    QueryCheck(
        error_code=270,
        level=CheckLevel.ERROR,
        column=models.PotentialBreach.id,
        invalid=Query(models.PotentialBreach)
        .join(models.Channel, models.Channel.id == models.PotentialBreach.channel_id)
        .filter(
            models.Channel.exchange_type.notin_(
                {
                    constants.CalculationType.CONNECTED,
                    constants.CalculationType.DOUBLE_CONNECTED,
                }
            )
        ),
        message="potential_breach is assigned to an isolated " "or embedded channel.",
    ),
    QueryCheck(
        error_code=271,
        level=CheckLevel.ERROR,
        column=models.PotentialBreach.id,
        invalid=Query(models.PotentialBreach)
        .join(models.Channel, models.Channel.id == models.PotentialBreach.channel_id)
        .filter(
            models.Channel.exchange_type == constants.CalculationType.CONNECTED,
        )
        .group_by(
            models.PotentialBreach.channel_id,
            func.PointN(models.PotentialBreach.geom, 1),
        )
        .having(func.count(models.PotentialBreach.id) > 1),
        message="channel can have max 1 potential_breach at the same position "
        "on a channel of connected (102) calculation type",
    ),
    QueryCheck(
        error_code=272,
        level=CheckLevel.ERROR,
        column=models.PotentialBreach.id,
        invalid=Query(models.PotentialBreach)
        .join(models.Channel, models.Channel.id == models.PotentialBreach.channel_id)
        .filter(
            models.Channel.exchange_type == constants.CalculationType.DOUBLE_CONNECTED,
        )
        .group_by(
            models.PotentialBreach.channel_id,
            func.PointN(models.PotentialBreach.geom, 1),
        )
        .having(func.count(models.PotentialBreach.id) > 2),
        message="channel can have max 2 potential_breach at the same position "
        "on a channel of double connected (105) calculation type",
    ),
    QueryCheck(
        error_code=273,
        level=CheckLevel.ERROR,
        column=models.PotentialBreach.id,
        invalid=Query(models.PotentialBreach)
        .join(models.Channel, models.Channel.id == models.PotentialBreach.channel_id)
        .filter(
            geo_func.ST_Distance(
                func.PointN(models.PotentialBreach.geom, 1), models.Channel.geom
            )
            > TOLERANCE_M
        ),
        message="potential_breach.geom must begin at the channel it is assigned to",
    ),
    PotentialBreachStartEndCheck(
        error_code=274,
        level=CheckLevel.ERROR,
        column=models.PotentialBreach.geom,
        min_distance=TOLERANCE_M,
    ),
    PotentialBreachInterdistanceCheck(
        error_code=275,
        level=CheckLevel.ERROR,
        column=models.PotentialBreach.geom,
        min_distance=TOLERANCE_M,
    ),
    RangeCheck(
        error_code=276,
        column=models.PotentialBreach.initial_exchange_level,
        min_value=-9998.0,
        max_value=8848.0,
    ),
    RangeCheck(
        error_code=277,
        column=models.PotentialBreach.final_exchange_level,
        min_value=-9998.0,
        max_value=8848.0,
        left_inclusive=False,
    ),
]


## 030x: SETTINGS

CHECKS += [
    QueryCheck(
        error_code=303,
        level=CheckLevel.WARNING,
        column=models.ModelSettings.use_1d_flow,
        invalid=Query(models.ModelSettings).filter(
            models.ModelSettings.use_1d_flow == False,
            Query(func.count(models.ConnectionNode.id) > 0).label("1d_count"),
        ),
        message="model_settings.use_1d_flow is turned off while there are 1D "
        "elements in the model",
    ),
    QueryCheck(
        error_code=304,
        column=models.ModelSettings.use_groundwater_flow,
        invalid=Query(models.ModelSettings).filter(
            models.ModelSettings.use_groundwater_flow == True,
            models.ModelSettings.use_simple_infiltration == True,
        ),
        message="simple_infiltration in combination with groundwater flow is not allowed.",
    ),
    RangeCheck(
        error_code=305,
        column=models.ModelSettings.nr_grid_levels,
        min_value=0,
        left_inclusive=False,  # 0 is not allowed
    ),
    RangeCheck(
        error_code=306,
        level=CheckLevel.WARNING,
        column=models.ModelSettings.calculation_point_distance_1d,
        min_value=0,
        left_inclusive=False,  # 0 itself is not allowed
        message="model_settings.calculation_point_distance_1d is not greater than 0, in the future this will lead to an error",
    ),
    RangeCheck(
        error_code=307,
        column=models.ModelSettings.minimum_cell_size,
        min_value=0,
        left_inclusive=False,  # 0 itself is not allowed
    ),
    RangeCheck(
        error_code=308,
        column=models.ModelSettings.embedded_cutoff_threshold,
        min_value=0,
    ),
    RangeCheck(
        error_code=309,
        column=models.ModelSettings.max_angle_1d_advection,
        min_value=0,
        max_value=0.5 * 3.14159,
    ),
    RangeCheck(
        error_code=310,
        column=models.ModelSettings.minimum_table_step_size,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=311,
        column=models.ModelSettings.table_step_size_1d,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=313,
        column=models.ModelSettings.friction_coefficient,
        filters=CONDITIONS["manning"].exists(),
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        error_code=314,
        column=models.ModelSettings.friction_coefficient,
        filters=CONDITIONS["chezy"].exists(),
        min_value=0,
    ),
    RangeCheck(
        error_code=315,
        column=models.Interception.interception,
        min_value=0,
    ),
    RangeCheck(
        error_code=316,
        column=models.ModelSettings.manhole_aboveground_storage_area,
        min_value=0,
    ),
    QueryCheck(
        error_code=319,
        column=models.ModelSettings.use_2d_flow,
        invalid=CONDITIONS["has_no_dem"].filter(
            models.ModelSettings.use_2d_flow == True
        ),
        message="model_settings.use_2d_flow may not be TRUE if no dem file is provided",
    ),
    QueryCheck(
        error_code=320,
        column=models.ModelSettings.use_2d_flow,
        invalid=Query(models.ModelSettings).filter(
            models.ModelSettings.use_1d_flow == False,
            models.ModelSettings.use_2d_flow == False,
        ),
        message="model_settings.use_1d_flow and model_settings.use_2d_flow cannot both be FALSE",
    ),
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=321,
        column=models.ModelSettings.manhole_aboveground_storage_area,
        invalid=Query(models.ModelSettings).filter(
            models.ModelSettings.manhole_aboveground_storage_area > 0,
            (
                (models.ModelSettings.use_2d_flow == True)
                | (~is_none_or_empty(models.ModelSettings.dem_file))
            ),
        ),
        message="sub-basins (model_settings.manhole_aboveground_storage_area > 0) should only be used when there is no DEM supplied and there is no 2D flow",
    ),
    QueryCheck(
        error_code=322,
        column=models.InitialConditions.initial_water_level_aggregation,
        invalid=Query(models.InitialConditions).filter(
            ~is_none_or_empty(models.InitialConditions.initial_water_level_file),
            models.InitialConditions.initial_water_level_aggregation == None,
        ),
        message="an initial waterlevel type (initial_conditions.initial_water_level_aggregation) should be defined when using an initial waterlevel file.",
    ),
    QueryCheck(
        error_code=323,
        column=models.ModelSettings.maximum_table_step_size,
        invalid=Query(models.ModelSettings).filter(
            models.ModelSettings.maximum_table_step_size
            < models.ModelSettings.minimum_table_step_size,
        ),
        message="model_settings.maximum_table_step_size should be greater than model_settings.minimum_table_step_size.",
    ),
    QueryCheck(
        error_code=325,
        level=CheckLevel.WARNING,
        column=models.Interception.interception,
        invalid=Query(models.Interception).filter(
            ~is_none_or_empty(models.Interception.interception_file),
            is_none_or_empty(models.Interception.interception),
        ),
        message="interception.interception is recommended as fallback value when using an interception_file.",
    ),
]

CHECKS += [
    UsedSettingsPresentCheckSingleTable(
        error_code=326, level=CheckLevel.ERROR, column=use_col, settings_table=table
    )
    for table, use_col in (
        (
            models.SimpleInfiltration,
            models.ModelSettings.use_simple_infiltration,
        ),
        (models.Interflow, models.ModelSettings.use_interflow),
        (models.GroundWater, models.ModelSettings.use_groundwater_flow),
        (models.GroundWater, models.ModelSettings.use_groundwater_storage),
        (models.VegetationDrag2D, models.ModelSettings.use_vegetation_drag_2d),
        (models.Interception, models.ModelSettings.use_interception),
    )
]

CHECKS += [
    QueryCheck(
        error_code=327,
        column=models.ModelSettings.use_vegetation_drag_2d,
        invalid=Query(models.ModelSettings).filter(
            models.ModelSettings.use_vegetation_drag_2d,
            models.ModelSettings.friction_type != constants.FrictionType.CHEZY.value,
        ),
        message="Vegetation drag can only be used in combination with friction type 1 (Chézy)",
    )
]

CHECKS += [
    MaxOneRecordCheck(column=table.id, level=CheckLevel.INFO, error_code=328)
    for table in [
        models.ModelSettings,
        models.SimulationTemplateSettings,
        models.TimeStepSettings,
        models.NumericalSettings,
        models.PhysicalSettings,
        models.InitialConditions,
        models.SimpleInfiltration,
        models.Interflow,
        models.GroundWater,
        models.VegetationDrag2D,
        models.Interception,
    ]
]

CHECKS += [
    RangeCheck(
        error_code=360,
        level=CheckLevel.WARNING,
        column=models.ModelSettings.calculation_point_distance_1d,
        min_value=5.0,
        left_inclusive=True,  # 0 itself is not allowed
        message="model_settings.calculation_point_distance_1d should preferably be at least 5.0 metres to prevent simulation timestep reduction.",
    )
]

CHECKS += [
    UsedSettingsPresentCheck(
        error_code=329,
        level=CheckLevel.FUTURE_ERROR,
        column=use_col,
        settings_tables=tables,
    )
    for tables, use_col in (
        (
            [models.Surface, models.DryWeatherFlow],
            models.SimulationTemplateSettings.use_0d_inflow,
        ),
        (
            [models.TableControl, models.MemoryControl],
            models.SimulationTemplateSettings.use_structure_control,
        ),
    )
]

## 04xx: Groundwater, Interflow & Infiltration
CHECKS += [
    RangeCheck(
        error_code=401,
        column=models.Interflow.porosity,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        error_code=402,
        column=models.Interflow.impervious_layer_elevation,
        min_value=0,
    ),
    RangeCheck(
        error_code=403,
        column=models.SimpleInfiltration.infiltration_rate,
        min_value=0,
    ),
    QueryCheck(
        error_code=404,
        column=models.SimpleInfiltration.infiltration_rate,
        invalid=Query(models.SimpleInfiltration).filter(
            models.SimpleInfiltration.infiltration_rate == None,
            is_none_or_empty(models.SimpleInfiltration.infiltration_rate_file),
        ),
        message="simple_infiltration.infiltration_rate must be defined.",
    ),
    QueryCheck(
        error_code=404,
        level=CheckLevel.WARNING,
        column=models.SimpleInfiltration.infiltration_rate,
        invalid=Query(models.SimpleInfiltration).filter(
            models.SimpleInfiltration.infiltration_rate == None,
            ~is_none_or_empty(models.SimpleInfiltration.infiltration_rate_file),
        ),
        message="simple_infiltration.infiltration_rate is recommended as fallback value when using an infiltration_rate_file.",
    ),
    QueryCheck(
        error_code=405,
        level=CheckLevel.WARNING,
        column=models.GroundWater.equilibrium_infiltration_rate,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.equilibrium_infiltration_rate == None,
            ~is_none_or_empty(models.GroundWater.equilibrium_infiltration_rate_file),
        ),
        message="groundwater.equilibrium_infiltration_rate is recommended as fallback value when using an equilibrium_infiltration_rate_file.",
    ),
    QueryCheck(
        error_code=406,
        column=models.GroundWater.equilibrium_infiltration_rate_aggregation,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.equilibrium_infiltration_rate_aggregation == None,
            ~is_none_or_empty(models.GroundWater.equilibrium_infiltration_rate_file),
        ),
        message="groundwater.equilibrium_infiltration_rate_aggregation should be defined when using an equilibrium_infiltration_rate_file.",
    ),
    QueryCheck(
        error_code=407,
        column=models.GroundWater.infiltration_decay_period,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.infiltration_decay_period == None,
            is_none_or_empty(models.GroundWater.infiltration_decay_period_file),
        ),
        message="groundwater.infiltration_decay_period must be defined when not using an infiltration_decay_period_file.",
    ),
    QueryCheck(
        error_code=407,
        level=CheckLevel.WARNING,
        column=models.GroundWater.infiltration_decay_period,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.infiltration_decay_period == None,
            ~is_none_or_empty(models.GroundWater.infiltration_decay_period_file),
        ),
        message="groundwater.infiltration_decay_period is recommended as fallback value when using an infiltration_decay_period_file.",
    ),
    QueryCheck(
        error_code=408,
        column=models.GroundWater.infiltration_decay_period_aggregation,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.infiltration_decay_period_aggregation == None,
            ~is_none_or_empty(models.GroundWater.infiltration_decay_period_file),
        ),
        message="an infiltration decay period type (groundwater.infiltration_decay_period_aggregation) should be defined when using an infiltration decay period file.",
    ),
    QueryCheck(
        error_code=409,
        column=models.GroundWater.groundwater_hydraulic_conductivity_aggregation,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.groundwater_hydraulic_conductivity_aggregation == None,
            ~is_none_or_empty(
                models.GroundWater.groundwater_hydraulic_conductivity_file
            ),
        ),
        message="groundwater.groundwater_hydraulic_conductivity_aggregation should be defined when using a groundwater_hydraulic_conductivity_file.",
    ),
    QueryCheck(
        error_code=410,
        column=models.GroundWater.groundwater_impervious_layer_level,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.groundwater_impervious_layer_level == None,
            is_none_or_empty(
                models.GroundWater.groundwater_impervious_layer_level_file
            ),
        ),
        message="groundwater.groundwater_impervious_layer_level must be defined when not using an groundwater_impervious_layer_level_file",
    ),
    QueryCheck(
        error_code=410,
        level=CheckLevel.WARNING,
        column=models.GroundWater.groundwater_impervious_layer_level,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.groundwater_impervious_layer_level == None,
            ~is_none_or_empty(
                models.GroundWater.groundwater_impervious_layer_level_file
            ),
        ),
        message="groundwater.groundwater_impervious_layer_level is recommended as fallback value when using a groundwater_impervious_layer_level_file.",
    ),
    QueryCheck(
        error_code=411,
        column=models.GroundWater.groundwater_impervious_layer_level_aggregation,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.groundwater_impervious_layer_level_aggregation == None,
            ~is_none_or_empty(
                models.GroundWater.groundwater_impervious_layer_level_file
            ),
        ),
        message="groundwater.groundwater_impervious_layer_level_aggregation should be defined when using a groundwater_impervious_layer_level_file",
    ),
    QueryCheck(
        error_code=412,
        column=models.GroundWater.initial_infiltration_rate,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.initial_infiltration_rate == None,
            is_none_or_empty(models.GroundWater.initial_infiltration_rate_file),
        ),
        message="groundwater.initial_infiltration_rate must be defined when not using a initial_infiltration_rate_file.",
    ),
    QueryCheck(
        error_code=412,
        level=CheckLevel.WARNING,
        column=models.GroundWater.initial_infiltration_rate,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.initial_infiltration_rate == None,
            ~is_none_or_empty(models.GroundWater.initial_infiltration_rate_file),
        ),
        message="groundwater.initial_infiltration_rate is recommended as fallback value when using a initial_infiltration_rate_file.",
    ),
    QueryCheck(
        error_code=413,
        column=models.GroundWater.initial_infiltration_rate_aggregation,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.initial_infiltration_rate_aggregation == None,
            ~is_none_or_empty(models.GroundWater.initial_infiltration_rate_file),
        ),
        message="groundwater.initial_infiltration_rate_aggregation should be defined when using an initial infiltration rate file.",
    ),
    QueryCheck(
        error_code=414,
        column=models.GroundWater.phreatic_storage_capacity,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.phreatic_storage_capacity == None,
            is_none_or_empty(models.GroundWater.phreatic_storage_capacity_file),
        ),
        message="groundwater.phreatic_storage_capacity must be defined when not using a phreatic_storage_capacity_file.",
    ),
    QueryCheck(
        error_code=414,
        level=CheckLevel.WARNING,
        column=models.GroundWater.phreatic_storage_capacity,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.phreatic_storage_capacity == None,
            ~is_none_or_empty(models.GroundWater.phreatic_storage_capacity_file),
        ),
        message="groundwater.phreatic_storage_capacity is recommended as fallback value when using a phreatic_storage_capacity_file.",
    ),
    QueryCheck(
        error_code=415,
        column=models.GroundWater.phreatic_storage_capacity_aggregation,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.phreatic_storage_capacity_aggregation == None,
            ~is_none_or_empty(models.GroundWater.phreatic_storage_capacity_file),
        ),
        message="a phreatic storage capacity type (groundwater.phreatic_storage_capacity_aggregation) should be defined when using a phreatic storage capacity file.",
    ),
    QueryCheck(
        error_code=416,
        column=models.Interflow.porosity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.porosity == None,
            is_none_or_empty(models.Interflow.porosity_file),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="interflow.porosity must be defined when not using a porosity_file.",
    ),
    QueryCheck(
        error_code=416,
        level=CheckLevel.WARNING,
        column=models.Interflow.porosity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.porosity == None,
            ~is_none_or_empty(models.Interflow.porosity_file),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="interflow.porosity is recommended as fallback value when using a porosity_file.",
    ),
    QueryCheck(
        error_code=417,
        column=models.Interflow.porosity_layer_thickness,
        invalid=Query(models.Interflow).filter(
            (models.Interflow.porosity_layer_thickness == None)
            | (models.Interflow.porosity_layer_thickness <= 0),
            models.Interflow.interflow_type
            in [
                constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY,
                constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY,
            ],
        ),
        message=f"a porosity layer thickness (interflow.porosity_layer_thickness) should be defined and >0 when "
        f"interflow_type is "
        f"{constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY} or "
        f"{constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY}",
    ),
    QueryCheck(
        error_code=418,
        column=models.Interflow.impervious_layer_elevation,
        invalid=Query(models.Interflow).filter(
            models.Interflow.impervious_layer_elevation == None,
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="interflow.impervious_layer_elevation cannot be null",
    ),
    QueryCheck(
        error_code=419,
        column=models.Interflow.hydraulic_conductivity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.hydraulic_conductivity == None,
            is_none_or_empty(models.Interflow.hydraulic_conductivity_file),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="interflow.hydraulic_conductivity must be defined when not using a hydraulic_conductivity_file.",
    ),
    QueryCheck(
        error_code=419,
        level=CheckLevel.WARNING,
        column=models.Interflow.hydraulic_conductivity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.hydraulic_conductivity == None,
            ~is_none_or_empty(models.Interflow.hydraulic_conductivity_file),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        ),
        message="interflow.hydraulic_conductivity is recommended as fallback value when using a hydraulic_conductivity_file.",
    ),
    RangeCheck(
        error_code=420,
        column=models.GroundWater.phreatic_storage_capacity,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        error_code=421,
        column=models.GroundWater.groundwater_hydraulic_conductivity,
        min_value=0,
    ),
    RangeCheck(
        error_code=422,
        column=models.SimpleInfiltration.max_infiltration_volume,
        min_value=0,
    ),
    QueryCheck(
        error_code=423,
        level=CheckLevel.WARNING,
        column=models.SimpleInfiltration.max_infiltration_volume,
        invalid=Query(models.SimpleInfiltration).filter(
            models.SimpleInfiltration.max_infiltration_volume == None,
            ~is_none_or_empty(models.SimpleInfiltration.max_infiltration_volume_file),
        ),
        message="simple_infiltration.max_infiltration_volume is recommended as fallback value when using an max_infiltration_volume_file.",
    ),
    RangeCheck(
        error_code=424,
        column=models.Interflow.hydraulic_conductivity,
        filters=(
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW
        ),
        min_value=0,
    ),
    RangeCheck(
        error_code=425,
        column=models.GroundWater.initial_infiltration_rate,
        min_value=0,
    ),
    RangeCheck(
        error_code=426,
        column=models.GroundWater.equilibrium_infiltration_rate,
        min_value=0,
    ),
    RangeCheck(
        error_code=427,
        column=models.GroundWater.infiltration_decay_period,
        min_value=0,
        left_inclusive=False,
    ),
    QueryCheck(
        error_code=428,
        level=CheckLevel.WARNING,
        column=models.GroundWater.groundwater_hydraulic_conductivity,
        invalid=Query(models.GroundWater).filter(
            (models.GroundWater.groundwater_hydraulic_conductivity == None),
            ~is_none_or_empty(
                models.GroundWater.groundwater_hydraulic_conductivity_file
            ),
        ),
        message="groundwater.groundwater_hydraulic_conductivity is recommended as fallback value when using a groundwater_hydraulic_conductivity_file.",
    ),
    RangeCheck(
        error_code=429,
        column=models.ConnectionNode.exchange_thickness,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=430,
        column=models.ConnectionNode.hydraulic_conductivity_in,
        min_value=0,
    ),
    RangeCheck(
        error_code=431,
        column=models.ConnectionNode.hydraulic_conductivity_out,
        min_value=0,
    ),
    RangeCheck(
        error_code=432,
        column=models.Channel.exchange_thickness,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=433,
        column=models.Channel.hydraulic_conductivity_in,
        min_value=0,
    ),
    RangeCheck(
        error_code=434,
        column=models.Channel.hydraulic_conductivity_out,
        min_value=0,
    ),
    RangeCheck(
        error_code=435,
        column=models.Pipe.exchange_thickness,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=436,
        column=models.Pipe.hydraulic_conductivity_in,
        min_value=0,
    ),
    RangeCheck(
        error_code=437,
        column=models.Pipe.hydraulic_conductivity_out,
        min_value=0,
    ),
]

## 05xx: VEGETATION DRAG
CHECKS += [
    RangeCheck(
        error_code=501,
        column=models.VegetationDrag2D.vegetation_height,
        min_value=0,
        left_inclusive=False,
    ),
    QueryCheck(
        error_code=502,
        column=models.VegetationDrag2D.vegetation_height,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_height == None,
            is_none_or_empty(models.VegetationDrag2D.vegetation_height_file),
        ),
        message="vegetation_drag.height must be defined.",
    ),
    QueryCheck(
        error_code=503,
        level=CheckLevel.WARNING,
        column=models.VegetationDrag2D.vegetation_height,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_height == None,
            ~is_none_or_empty(models.VegetationDrag2D.vegetation_height_file),
        ),
        message="vegetation_drag.height is recommended as fallback value when using a vegetation_height_file.",
    ),
    RangeCheck(
        error_code=504,
        column=models.VegetationDrag2D.vegetation_stem_count,
        min_value=0,
        left_inclusive=False,
    ),
    QueryCheck(
        error_code=505,
        column=models.VegetationDrag2D.vegetation_stem_count,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_stem_count == None,
            is_none_or_empty(models.VegetationDrag2D.vegetation_stem_count_file),
        ),
        message="vegetation_drag.vegetation_stem_count must be defined.",
    ),
    QueryCheck(
        error_code=506,
        level=CheckLevel.WARNING,
        column=models.VegetationDrag2D.vegetation_stem_count,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_stem_count == None,
            ~is_none_or_empty(models.VegetationDrag2D.vegetation_stem_count_file),
        ),
        message="vegetation_drag.vegetation_stem_count is recommended as fallback value when using a vegetation_stem_count_file.",
    ),
    RangeCheck(
        error_code=507,
        column=models.VegetationDrag2D.vegetation_stem_diameter,
        min_value=0,
        left_inclusive=False,
    ),
    QueryCheck(
        error_code=508,
        column=models.VegetationDrag2D.vegetation_stem_diameter,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_stem_diameter == None,
            is_none_or_empty(models.VegetationDrag2D.vegetation_stem_diameter_file),
        ),
        message="vegetation_drag.vegetation_stem_diameter must be defined.",
    ),
    QueryCheck(
        error_code=509,
        level=CheckLevel.WARNING,
        column=models.VegetationDrag2D.vegetation_stem_diameter,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_stem_diameter == None,
            ~is_none_or_empty(models.VegetationDrag2D.vegetation_stem_diameter_file),
        ),
        message="vegetation_drag.vegetation_stem_diameter is recommended as fallback value when using a vegetation_stem_diameter_file.",
    ),
    RangeCheck(
        error_code=510,
        column=models.VegetationDrag2D.vegetation_drag_coefficient,
        min_value=0,
        left_inclusive=False,
    ),
    QueryCheck(
        error_code=511,
        column=models.VegetationDrag2D.vegetation_drag_coefficient,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_drag_coefficient == None,
            is_none_or_empty(models.VegetationDrag2D.vegetation_drag_coefficient_file),
        ),
        message="vegetation_drag.vegetation_drag_coefficient must be defined.",
    ),
    QueryCheck(
        error_code=512,
        level=CheckLevel.WARNING,
        column=models.VegetationDrag2D.vegetation_drag_coefficient,
        invalid=Query(models.VegetationDrag2D).filter(
            models.VegetationDrag2D.vegetation_drag_coefficient == None,
            ~is_none_or_empty(models.VegetationDrag2D.vegetation_drag_coefficient_file),
        ),
        message="vegetation_drag.vegetation_drag_coefficient is recommended as fallback value when using a vegetation_drag_coefficient_file.",
    ),
]

## 06xx: INFLOW
CHECKS += [
    RangeCheck(
        error_code=601 + i,
        column=column,
        min_value=0,
        filters=CONDITIONS["has_inflow"].exists(),
    )
    for i, column in enumerate(
        [models.DryWeatherFlow.multiplier, models.DryWeatherFlow.daily_total]
    )
]

CHECKS += [
    RangeCheck(
        error_code=603,
        column=models.Surface.area,
        min_value=0,
        filters=CONDITIONS["has_inflow"].exists(),
    )
]

CHECKS += [
    RangeCheck(
        error_code=604,
        column=map_table.percentage,
        min_value=0,
        filters=CONDITIONS["has_inflow"].exists(),
    )
    for i, map_table in enumerate([models.DryWeatherFlowMap, models.SurfaceMap])
]

CHECKS += [
    RangeCheck(
        error_code=code,
        column=models.SurfaceParameters.outflow_delay,
        min_value=0,
        filters=CONDITIONS["has_inflow"].exists(),
    )
    for code, column in [
        (606, models.SurfaceParameters.outflow_delay),
        (607, models.SurfaceParameters.max_infiltration_capacity),
        (608, models.SurfaceParameters.min_infiltration_capacity),
        (609, models.SurfaceParameters.infiltration_decay_constant),
        (610, models.SurfaceParameters.infiltration_recovery_constant),
    ]
]
CHECKS += [Use0DFlowCheck(error_code=611, level=CheckLevel.WARNING)]

CHECKS += [
    QueryCheck(
        level=CheckLevel.WARNING,
        error_code=612,
        column=map_table.connection_node_id,
        filters=CONDITIONS["has_inflow"].exists(),
        invalid=Query(map_table).filter(
            map_table.connection_node_id.in_(
                Query(models.BoundaryCondition1D.connection_node_id)
            ),
        ),
        message=f"{map_table.__tablename__} will be ignored because it is connected to a 1D boundary condition.",
    )
    for map_table in [models.DryWeatherFlowMap, models.SurfaceMap]
]

CHECKS += [
    SurfaceNodeInflowAreaCheck(
        error_code=613,
        level=CheckLevel.WARNING,
        filters=CONDITIONS["has_inflow"].exists(),
    ),
]
CHECKS += [
    NodeSurfaceConnectionsCheck(
        error_code=614,
        level=CheckLevel.WARNING,
        filters=CONDITIONS["has_inflow"].exists(),
    )
]


CHECKS += [
    QueryCheck(
        error_code=616,
        level=CheckLevel.WARNING,
        column=table.id,
        filters=~CONDITIONS["has_inflow"].exists(),
        invalid=Query(table),
        message=f"No inflow will be generated for this feature, because model_settings.use_0d_inflow is not set to use {table.__tablename__}.",
    )
    for table in [models.DryWeatherFlow, models.Surface]
]

CHECKS += [
    InflowNoFeaturesCheck(
        error_code=617,
        level=CheckLevel.WARNING,
        feature_table=table,
        condition=CONDITIONS["has_inflow"].exists(),
    )
    for table in [models.DryWeatherFlow, models.Surface]
]

CHECKS += [
    QueryCheck(
        error_code=618 + i,
        level=CheckLevel.WARNING,
        column=column,
        invalid=Query(table).filter(column == None),
        filters=CONDITIONS["has_inflow"].exists(),
        message=f"{table.__tablename__}.{column.name} cannot be Null",
    )
    for i, (table, column) in enumerate(
        [
            (models.Surface, models.Surface.area),
            (models.DryWeatherFlow, models.DryWeatherFlow.multiplier),
            (models.DryWeatherFlow, models.DryWeatherFlow.daily_total),
        ]
    )
]

# Dry weather flow distribution
CHECKS += [
    DWFDistributionCSVFormatCheck(error_code=621),
    DWFDistributionLengthCheck(error_code=622),
    DWFDistributionSumCheck(error_code=623),
]


# 07xx: RASTERS
RASTER_COLUMNS = [
    models.ModelSettings.dem_file,
    models.ModelSettings.friction_coefficient_file,
    models.Interception.interception_file,
    models.Interflow.porosity_file,
    models.Interflow.hydraulic_conductivity_file,
    models.SimpleInfiltration.infiltration_rate_file,
    models.SimpleInfiltration.max_infiltration_volume_file,
    models.GroundWater.groundwater_impervious_layer_level_file,
    models.GroundWater.phreatic_storage_capacity_file,
    models.GroundWater.equilibrium_infiltration_rate_file,
    models.GroundWater.initial_infiltration_rate_file,
    models.GroundWater.infiltration_decay_period_file,
    models.GroundWater.groundwater_hydraulic_conductivity_file,
    models.GroundWater.leakage_file,
    models.InitialConditions.initial_water_level_file,
    models.InitialConditions.initial_groundwater_level_file,
    models.VegetationDrag2D.vegetation_height_file,
    models.VegetationDrag2D.vegetation_stem_count_file,
    models.VegetationDrag2D.vegetation_stem_diameter_file,
    models.VegetationDrag2D.vegetation_drag_coefficient_file,
]

CHECKS += [
    GDALAvailableCheck(
        error_code=700, level=CheckLevel.WARNING, column=models.ModelSettings.dem_file
    )
]
CHECKS += [
    RasterExistsCheck(
        error_code=701 + i,
        column=column,
    )
    for i, column in enumerate(RASTER_COLUMNS)
]
CHECKS += [
    RasterIsValidCheck(
        error_code=721 + i,
        column=column,
    )
    for i, column in enumerate(RASTER_COLUMNS)
]
CHECKS += [
    RasterHasOneBandCheck(
        error_code=741 + i,
        level=CheckLevel.WARNING,
        column=column,
    )
    for i, column in enumerate(RASTER_COLUMNS)
]
CHECKS += [
    RasterSquareCellsCheck(
        error_code=780,
        column=models.ModelSettings.dem_file,
    ),
    RasterRangeCheck(
        error_code=781,
        column=models.ModelSettings.dem_file,
        min_value=-9998.0,
        max_value=8848.0,
    ),
    RasterRangeCheck(
        error_code=782,
        column=models.ModelSettings.friction_coefficient_file,
        filters=CONDITIONS["manning"].exists(),
        min_value=0,
        max_value=1,
    ),
    RasterRangeCheck(
        error_code=783,
        column=models.ModelSettings.friction_coefficient_file,
        filters=CONDITIONS["chezy"].exists(),
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=784,
        column=models.Interflow.porosity_file,
        min_value=0,
        max_value=1,
    ),
    RasterRangeCheck(
        error_code=785,
        column=models.Interflow.hydraulic_conductivity_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=786,
        column=models.SimpleInfiltration.infiltration_rate_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=787,
        column=models.SimpleInfiltration.max_infiltration_volume_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=788,
        column=models.GroundWater.groundwater_impervious_layer_level_file,
        min_value=-9998.0,
        max_value=8848.0,
    ),
    RasterRangeCheck(
        error_code=789,
        column=models.GroundWater.phreatic_storage_capacity_file,
        min_value=0,
        max_value=1,
    ),
    RasterRangeCheck(
        error_code=790,
        column=models.GroundWater.equilibrium_infiltration_rate_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=791,
        column=models.GroundWater.initial_infiltration_rate_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=792,
        column=models.GroundWater.infiltration_decay_period_file,
        min_value=0,
        left_inclusive=False,
    ),
    RasterRangeCheck(
        error_code=793,
        column=models.GroundWater.groundwater_hydraulic_conductivity_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=795,
        column=models.InitialConditions.initial_water_level_file,
        min_value=-9998.0,
        max_value=8848.0,
    ),
    RasterRangeCheck(
        error_code=796,
        column=models.InitialConditions.initial_groundwater_level_file,
        filters=models.InitialConditions.id != None,
        min_value=-9998.0,
        max_value=8848.0,
    ),
    RasterGridSizeCheck(
        error_code=798,
        column=models.ModelSettings.dem_file,
    ),
    RasterRangeCheck(
        error_code=799,
        level=CheckLevel.WARNING,
        column=models.ModelSettings.friction_coefficient_file,
        filters=CONDITIONS["chezy"].exists(),
        min_value=1,
        message=f"Some pixels in {models.ModelSettings.__tablename__}.{models.ModelSettings.friction_coefficient_file.name} are less than 1, while friction type is Chézy. This may lead to unexpected results. Did you mean to use friction type Manning?",
    ),
    ## 100xx: We continue raster checks from 1400
    RasterRangeCheck(
        error_code=1401,
        column=models.VegetationDrag2D.vegetation_height_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=1402,
        column=models.VegetationDrag2D.vegetation_stem_count_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=1403,
        column=models.VegetationDrag2D.vegetation_stem_diameter_file,
        min_value=0,
    ),
    RasterRangeCheck(
        error_code=1404,
        column=models.VegetationDrag2D.vegetation_drag_coefficient_file,
        min_value=0,
    ),
    RasterPixelCountCheck(
        error_code=1405,
        column=models.ModelSettings.dem_file,
    ),
]

CHECKS += [
    RasterCompressionUsedCheck(
        error_code=1406,
        level=CheckLevel.INFO,
        column=column,
    )
    for column in (
        models.Interflow.porosity_file,
        models.Interflow.hydraulic_conductivity_file,
        models.SimpleInfiltration.infiltration_rate_file,
        models.SimpleInfiltration.max_infiltration_volume_file,
        models.GroundWater.groundwater_impervious_layer_level_file,
        models.GroundWater.phreatic_storage_capacity_file,
        models.GroundWater.equilibrium_infiltration_rate_file,
        models.GroundWater.initial_infiltration_rate_file,
        models.GroundWater.infiltration_decay_period_file,
        models.GroundWater.groundwater_hydraulic_conductivity_file,
        models.GroundWater.leakage_file,
        models.VegetationDrag2D.vegetation_height_file,
        models.VegetationDrag2D.vegetation_stem_count_file,
        models.VegetationDrag2D.vegetation_stem_diameter_file,
        models.VegetationDrag2D.vegetation_drag_coefficient_file,
        models.ModelSettings.dem_file,
        models.ModelSettings.friction_coefficient_file,
        models.InitialConditions.initial_water_level_file,
        models.Interception.interception_file,
        models.InitialConditions.initial_groundwater_level_file,
    )
]

## 080x: refinement levels
CHECKS += [
    QueryCheck(
        error_code=800,
        level=CheckLevel.FUTURE_ERROR,
        column=model.grid_level,
        invalid=Query(model).filter(model.grid_level > nr_grid_levels),
        message=f"{model.__table__.name}.refinement_level must not be greater than model_settings.nr_grid_levels",
    )
    for model in (models.GridRefinementLine, models.GridRefinementArea)
]
CHECKS += [
    RangeCheck(
        error_code=801,
        column=model.grid_level,
        min_value=1,
    )
    for model in (models.GridRefinementLine, models.GridRefinementArea)
]
CHECKS += [
    QueryCheck(
        error_code=802,
        level=CheckLevel.INFO,
        column=model.grid_level,
        invalid=Query(model).filter(model.grid_level == nr_grid_levels),
        message=f"{model.__table__.name}.refinement_level is equal to model_settings.nr_grid_levels and will "
        "therefore not have any effect. Lower the refinement_level to make the cells smaller.",
    )
    for model in (models.GridRefinementLine, models.GridRefinementArea)
]

## 110x: SIMULATION SETTINGS, timestep
CHECKS += [
    QueryCheck(
        error_code=1101,
        column=models.TimeStepSettings.max_time_step,
        invalid=Query(models.TimeStepSettings).filter(
            models.TimeStepSettings.max_time_step < models.TimeStepSettings.time_step
        ),
        message="time_step_settings.max_time_step must be greater than or equal to time_step_settings.time_step",
    ),
    QueryCheck(
        error_code=1102,
        column=models.TimeStepSettings.time_step,
        invalid=Query(models.TimeStepSettings).filter(
            models.TimeStepSettings.min_time_step > models.TimeStepSettings.time_step
        ),
        message="time_step_settings.mintime_step must be less than or equal to time_step_settings.time_step",
    ),
    QueryCheck(
        error_code=1103,
        column=models.TimeStepSettings.output_time_step,
        invalid=Query(models.TimeStepSettings).filter(
            models.TimeStepSettings.output_time_step < models.TimeStepSettings.time_step
        ),
        message="time_step_settings.output_time_step must be greater than or equal to time_step_settings.time_step",
    ),
    QueryCheck(
        error_code=1104,
        column=models.TimeStepSettings.max_time_step,
        invalid=Query(models.TimeStepSettings).filter(
            models.TimeStepSettings.use_time_step_stretch == True,
            models.TimeStepSettings.max_time_step == None,
        ),
        message="time_step_settings.max_time_step cannot be null when "
        "time_step_settings.use_time_step_stretch is True",
    ),
]
CHECKS += [
    RangeCheck(
        error_code=1105,
        column=getattr(models.TimeStepSettings, name),
        min_value=0,
        left_inclusive=False,
    )
    for name in (
        "time_step",
        "min_time_step",
        "max_time_step",
        "output_time_step",
    )
]
CHECKS += [
    QueryCheck(
        error_code=1106,
        level=CheckLevel.WARNING,
        column=models.TimeStepSettings.min_time_step,
        invalid=Query(models.TimeStepSettings).filter(
            models.TimeStepSettings.min_time_step
            > (0.1 * models.TimeStepSettings.time_step)
        ),
        message="time_step_settings.min_time_step should be at least 10 times smaller than time_step_settings.time_step",
    )
]

## 111x - 114x: SIMULATION SETTINGS, numerical
CHECKS += [
    RangeCheck(
        error_code=1110,
        column=models.NumericalSettings.cfl_strictness_factor_1d,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=1111,
        column=models.NumericalSettings.cfl_strictness_factor_2d,
        min_value=0,
        left_inclusive=False,
    ),
    RangeCheck(
        error_code=1112,
        column=models.NumericalSettings.convergence_eps,
        min_value=1e-7,
        max_value=1e-4,
    ),
    RangeCheck(
        error_code=1113,
        column=models.NumericalSettings.convergence_cg,
        min_value=1e-12,
        max_value=1e-7,
    ),
    RangeCheck(
        error_code=1114,
        column=models.NumericalSettings.flow_direction_threshold,
        min_value=1e-13,
        max_value=1e-2,
    ),
    RangeCheck(
        error_code=1115,
        column=models.NumericalSettings.general_numerical_threshold,
        min_value=1e-13,
        max_value=1e-7,
    ),
    RangeCheck(
        error_code=1116,
        column=models.NumericalSettings.max_non_linear_newton_iterations,
        min_value=1,
    ),
    RangeCheck(
        error_code=1117,
        column=models.NumericalSettings.max_degree_gauss_seidel,
        min_value=1,
    ),
    RangeCheck(
        error_code=1118,
        column=models.NumericalSettings.min_friction_velocity,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        error_code=1119,
        column=models.NumericalSettings.min_surface_area,
        min_value=1e-13,
        max_value=1e-7,
    ),
    RangeCheck(
        error_code=1120,
        column=models.NumericalSettings.preissmann_slot,
        min_value=0,
    ),
    RangeCheck(
        error_code=1121,
        column=models.NumericalSettings.pump_implicit_ratio,
        min_value=0,
        max_value=1,
    ),
    RangeCheck(
        error_code=1122,
        column=models.NumericalSettings.limiter_slope_thin_water_layer,
        min_value=0,
    ),
    RangeCheck(
        error_code=1123,
        column=models.NumericalSettings.use_of_cg,
        min_value=1,
    ),
    RangeCheck(
        error_code=1124,
        column=models.NumericalSettings.flooding_threshold,
        min_value=0,
        max_value=0.05,
    ),
    QueryCheck(
        error_code=1125,
        column=models.NumericalSettings.limiter_slope_thin_water_layer,
        invalid=Query(models.NumericalSettings).filter(
            (models.NumericalSettings.friction_shallow_water_depth_correction == 3)
            & (models.NumericalSettings.limiter_slope_thin_water_layer <= 0)
        ),
        message="numerical_settings.limiter_slope_thin_water_layer must be greater than 0 when using friction_shallow_water_depth_correction option 3.",
    ),
    QueryCheck(
        error_code=1126,
        column=models.NumericalSettings.limiter_slope_thin_water_layer,
        invalid=Query(models.NumericalSettings).filter(
            (models.NumericalSettings.limiter_slope_crossectional_area_2d == 3)
            & (models.NumericalSettings.limiter_slope_thin_water_layer <= 0)
        ),
        message="numerical_settings.limiter_slope_thin_water_layer must be greater than 0 when using limiter_slope_crossectional_area_2d option 3.",
    ),
    QueryCheck(
        error_code=1127,
        column=models.NumericalSettings.limiter_slope_thin_water_layer,
        invalid=Query(models.NumericalSettings).filter(
            (models.NumericalSettings.limiter_slope_friction_2d == 0)
            & (models.NumericalSettings.limiter_slope_crossectional_area_2d != 0)
        ),
        message="numerical_settings.limiter_slope_friction_2d may not be 0 when using limiter_slope_crossectional_area_2d.",
    ),
]


## 115x SIMULATION SETTINGS, aggregation

CHECKS += [
    QueryCheck(
        error_code=1150,
        column=models.AggregationSettings.aggregation_method,
        invalid=Query(models.AggregationSettings).filter(
            (models.AggregationSettings.aggregation_method == "current")
            & (
                models.AggregationSettings.flow_variable.notin_(
                    ("volume", "interception")
                )
            )
        ),
        message="aggregation_settings.aggregation_method can only be 'current' for 'volume' or 'interception' flow_variables.",
    ),
    UniqueCheck(
        error_code=1151,
        level=CheckLevel.WARNING,
        columns=(
            models.AggregationSettings.flow_variable,
            models.AggregationSettings.aggregation_method,
        ),
    ),
    AllEqualCheck(
        error_code=1152,
        level=CheckLevel.WARNING,
        column=models.AggregationSettings.interval,
    ),
    QueryCheck(
        error_code=1153,
        level=CheckLevel.WARNING,
        column=models.AggregationSettings.interval,
        invalid=Query(models.AggregationSettings)
        .join(models.TimeStepSettings, true())
        .filter(
            models.AggregationSettings.interval
            < models.TimeStepSettings.output_time_step
        ),
        message="aggregation_settings.timestep is smaller than time_step_settings.output_time_step",
    ),
]
CHECKS += [
    CorrectAggregationSettingsExist(
        error_code=1154,
        level=CheckLevel.WARNING,
        aggregation_method=aggregation_method,
        flow_variable=flow_variable,
    )
    for (aggregation_method, flow_variable) in (
        (constants.AggregationMethod.CUMULATIVE, constants.FlowVariable.PUMP_DISCHARGE),
        (
            constants.AggregationMethod.CUMULATIVE,
            constants.FlowVariable.LATERAL_DISCHARGE,
        ),
        (
            constants.AggregationMethod.CUMULATIVE,
            constants.FlowVariable.SIMPLE_INFILTRATION,
        ),
        (constants.AggregationMethod.CUMULATIVE, constants.FlowVariable.RAIN),
        (constants.AggregationMethod.CUMULATIVE, constants.FlowVariable.LEAKAGE),
        (constants.AggregationMethod.CURRENT, constants.FlowVariable.INTERCEPTION),
        (constants.AggregationMethod.CUMULATIVE, constants.FlowVariable.DISCHARGE),
        (
            constants.AggregationMethod.CUMULATIVE_NEGATIVE,
            constants.FlowVariable.DISCHARGE,
        ),
        (
            constants.AggregationMethod.CUMULATIVE_POSITIVE,
            constants.FlowVariable.DISCHARGE,
        ),
        (constants.AggregationMethod.CURRENT, constants.FlowVariable.VOLUM),
        (
            constants.AggregationMethod.CUMULATIVE_NEGATIVE,
            constants.FlowVariable.SURFACE_SOURCE_SINK_DISCHARGE,
        ),
        (
            constants.AggregationMethod.CUMULATIVE_POSITIVE,
            constants.FlowVariable.SURFACE_SOURCE_SINK_DISCHARGE,
        ),
    )
]

## 12xx  SIMULATION, timeseries
CHECKS += [
    TimeseriesRowCheck(col, error_code=1200)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
        models.Lateral1D.timeseries,
        models.Lateral2D.timeseries,
    ]
]
CHECKS += [
    TimeseriesTimestepCheck(col, error_code=1201)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
        models.Lateral1D.timeseries,
        models.Lateral2D.timeseries,
    ]
]
CHECKS += [
    TimeseriesValueCheck(col, error_code=1202)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
        models.Lateral1D.timeseries,
        models.Lateral2D.timeseries,
    ]
]
CHECKS += [
    TimeseriesIncreasingCheck(col, error_code=1203)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
        models.Lateral1D.timeseries,
        models.Lateral2D.timeseries,
    ]
]
CHECKS += [
    TimeseriesStartsAtZeroCheck(col, error_code=1204)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
    ]
]
CHECKS += [
    TimeseriesExistenceCheck(col, error_code=1205)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
    ]
]
CHECKS += [
    TimeSeriesEqualTimestepsCheck(col, error_code=1206)
    for col in [
        models.BoundaryCondition1D.timeseries,
        models.BoundaryConditions2D.timeseries,
    ]
]
CHECKS += [FirstTimeSeriesEqualTimestepsCheck(error_code=1206)]


CHECKS += [
    QueryCheck(
        error_code=1227,
        column=models.MeasureMap.id,
        invalid=Query(models.MeasureMap).filter(
            (
                (models.MeasureMap.control_type == "memory")
                & models.MeasureMap.control_id.not_in(Query(models.MemoryControl.id))
            )
            | (
                (models.MeasureMap.control_type == "table")
                & models.MeasureMap.control_id.not_in(Query(models.TableControl.id))
            )
        ),
        message="control_measure_map.control_id references an id in memory_control or table_control, but the table it references does not contain an entry with that id.",
    )
]

CHECKS += [
    ControlHasSingleMeasureVariable(error_code=1229, control_model=table)
    for table in [models.TableControl, models.MemoryControl]
]


## 018x cross section parameters (continues 008x)
CHECKS += [
    QueryCheck(
        error_code=180,
        column=col,
        invalid=Query(models.CrossSectionLocation)
        .filter(
            models.CrossSectionLocation.cross_section_shape
            != constants.CrossSectionShape.TABULATED_YZ
        )
        .filter(col.is_not(None)),
        message=(
            f"{col.table.name}.{col.name} can only be used in combination with "
            f"a {constants.CrossSectionShape.TABULATED_YZ.name} cross section shape"
        ),
    )
    for col in [
        models.CrossSectionLocation.cross_section_friction_values,
        models.CrossSectionLocation.cross_section_vegetation_table,
    ]
]

CHECKS += [
    CrossSectionFrictionCorrectLengthCheck(
        error_code=181,
        column=models.CrossSectionLocation.cross_section_friction_values,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
        filters=models.CrossSectionLocation.cross_section_table.is_not(None)
        & models.CrossSectionLocation.cross_section_friction_values.is_not(None),
    )
]

CHECKS += [
    QueryCheck(
        error_code=182,
        level=CheckLevel.WARNING,
        column=col,
        invalid=Query(models.CrossSectionLocation)
        .filter(
            col.is_not(None)
            & models.CrossSectionLocation.cross_section_vegetation_table.is_not(None)
        )
        .filter(
            models.CrossSectionLocation.friction_type.is_(constants.FrictionType.CHEZY)
        ),
        message=(
            f"Both cross_section_location.{col.name} and cross_section_location.cross_section_vegetation_table "
            f"defined without conveyance; cross_section_location.{col.name} will be used"
        ),
    )
    for col in [
        models.CrossSectionLocation.vegetation_drag_coefficient,
        models.CrossSectionLocation.vegetation_height,
        models.CrossSectionLocation.vegetation_stem_diameter,
        models.CrossSectionLocation.vegetation_stem_density,
    ]
]

CHECKS += [
    QueryCheck(
        error_code=183,
        level=CheckLevel.WARNING,
        column=col,
        invalid=Query(models.CrossSectionLocation)
        .filter(
            col.is_not(None)
            & models.CrossSectionLocation.cross_section_vegetation_table.is_not(None)
        )
        .filter(
            models.CrossSectionLocation.friction_type.is_(
                constants.FrictionType.CHEZY_CONVEYANCE
            )
        ),
        message=(
            f"Both cross_section_location.{col.name} and cross_section_location.cross_section_vegetation_table "
            f"defined with conveyance; cross_section_location.cross_section_vegetation_table will be used"
        ),
    )
    for col in [
        models.CrossSectionLocation.vegetation_drag_coefficient,
        models.CrossSectionLocation.vegetation_height,
        models.CrossSectionLocation.vegetation_stem_diameter,
        models.CrossSectionLocation.vegetation_stem_density,
    ]
]

CHECKS += [
    QueryCheck(
        error_code=184,
        level=CheckLevel.WARNING,
        column=models.CrossSectionLocation.cross_section_friction_values,
        invalid=(
            Query(models.CrossSectionLocation)
            .filter(
                (
                    models.CrossSectionLocation.friction_type
                    == constants.FrictionType.CHEZY
                )
                | (
                    models.CrossSectionLocation.friction_type
                    == constants.FrictionType.MANNING
                )
            )
            .filter(
                models.CrossSectionLocation.cross_section_friction_values.is_not(None)
                & models.CrossSectionLocation.friction_value.is_not(None)
            )
        ),
        message="Both cross_section_location.cross_section_friction_values and cross_section_location.friction_value "
        "are defined for non-conveyance friction. Only cross_section_location.cross_section_friction_values will be used",
    ),
    QueryCheck(
        error_code=185,
        level=CheckLevel.WARNING,
        column=models.CrossSectionLocation.cross_section_friction_values,
        invalid=(
            Query(models.CrossSectionLocation)
            .filter(
                (
                    models.CrossSectionLocation.friction_type
                    == constants.FrictionType.CHEZY_CONVEYANCE
                )
                | (
                    models.CrossSectionLocation.friction_type
                    == constants.FrictionType.MANNING_CONVEYANCE
                )
            )
            .filter(
                models.CrossSectionLocation.cross_section_friction_values.is_not(None)
                & models.CrossSectionLocation.friction_value.is_not(None)
            )
        ),
        message="Both cross_section_location.cross_section_friction_values and cross_section_location.friction_value "
        "are defined for non-conveyance friction. Only cross_section_location.friction_value will be used",
    ),
]

## Friction values range
CHECKS += [
    CrossSectionVariableFrictionRangeCheck(
        min_value=0,
        max_value=1,
        right_inclusive=False,
        error_code=188,
        column=models.CrossSectionLocation.cross_section_friction_values,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
        friction_types=[
            constants.FrictionType.MANNING.value,
            constants.FrictionType.MANNING_CONVEYANCE.value,
        ],
    )
]
CHECKS += [
    CrossSectionVariableFrictionRangeCheck(
        min_value=0,
        error_code=189,
        column=models.CrossSectionLocation.cross_section_friction_values,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
        friction_types=[
            constants.FrictionType.CHEZY.value,
            constants.FrictionType.CHEZY_CONVEYANCE.value,
        ],
    )
]

## 019x vegetation parameter checks
vegetation_parameter_columns_singular = [
    models.CrossSectionLocation.vegetation_drag_coefficient,
    models.CrossSectionLocation.vegetation_height,
    models.CrossSectionLocation.vegetation_stem_diameter,
    models.CrossSectionLocation.vegetation_stem_density,
]

CHECKS += [
    RangeCheck(
        error_code=190,
        column=col,
        min_value=0,
    )
    for col in vegetation_parameter_columns_singular
]

CHECKS += [
    CrossSectionVegetationTableNotNegativeCheck(
        error_code=191,
        column=models.CrossSectionLocation.cross_section_vegetation_table,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
    )
]

CHECKS += [
    QueryCheck(
        error_code=192,
        column=col,
        invalid=Query(models.CrossSectionLocation)
        .filter(
            models.CrossSectionLocation.friction_type.in_(
                [
                    constants.FrictionType.MANNING,
                    constants.FrictionType.MANNING_CONVEYANCE,
                ]
            )
        )
        .filter(col.is_not(None)),
        message=(
            f"{col.table.name}.{col.name} cannot be used with Manning type friction"
        ),
    )
    for col in vegetation_parameter_columns_singular
]
CHECKS += [
    QueryCheck(
        error_code=193,
        column=models.CrossSectionLocation.cross_section_vegetation_table,
        invalid=(
            Query(models.CrossSectionLocation).filter(
                models.CrossSectionLocation.friction_type.in_(
                    [
                        constants.FrictionType.MANNING,
                        constants.FrictionType.MANNING_CONVEYANCE,
                    ]
                )
                & models.CrossSectionLocation.cross_section_vegetation_table.is_not(
                    None
                )
            )
        ),
        message=(
            "cross_section_location.cross_section_vegetation_table cannot be used with MANNING type friction"
        ),
    )
]
CHECKS += [
    AllPresentVegetationParameters(
        error_code=194,
        column=models.CrossSectionLocation.vegetation_height,
    ),
]
CHECKS += [
    CrossSectionTableCheck(
        column=models.CrossSectionLocation.cross_section_vegetation_table,
        error_code=195,
        shapes=(
            constants.CrossSectionShape.TABULATED_YZ,
            constants.CrossSectionShape.TABULATED_RECTANGLE,
            constants.CrossSectionShape.TABULATED_TRAPEZIUM,
        ),
        ncol=4,
    ),
    CrossSectionVegetationCorrectLengthCheck(
        column=models.CrossSectionLocation.cross_section_vegetation_table,
        error_code=196,
        filters=models.CrossSectionLocation.cross_section_vegetation_table.is_not(None),
        shapes=(
            constants.CrossSectionShape.TABULATED_YZ,
            constants.CrossSectionShape.TABULATED_RECTANGLE,
            constants.CrossSectionShape.TABULATED_TRAPEZIUM,
        ),
    ),
]


# Checks for nonsensical Chezy friction values
CHECKS += [
    RangeCheck(
        error_code=1500,
        level=CheckLevel.WARNING,
        column=table.friction_value,
        filters=table.friction_type == constants.FrictionType.CHEZY.value,
        min_value=1,
        message=f"{table.__tablename__}.friction_value is less than 1, while friction type is Chézy. This may lead to unexpected results. Did you mean to use friction type Manning?",
    )
    for table in [
        models.CrossSectionLocation,
        models.Culvert,
        models.Pipe,
    ]
]
CHECKS += [
    RangeCheck(
        error_code=1500,
        level=CheckLevel.WARNING,
        column=table.friction_value,
        filters=(table.friction_type == constants.FrictionType.CHEZY.value)
        & (table.crest_type == constants.CrestType.BROAD_CRESTED.value),
        min_value=1,
        message=f"{table.__tablename__}.friction_value is less than 1, while friction type is Chézy. This may lead to unexpected results. Did you mean to use friction type Manning?",
    )
    for table in [
        models.Orifice,
        models.Weir,
    ]
]
CHECKS += [
    CrossSectionVariableFrictionRangeCheck(
        min_value=1,
        level=CheckLevel.WARNING,
        error_code=1501,
        column=models.CrossSectionLocation.cross_section_friction_values,
        shapes=(constants.CrossSectionShape.TABULATED_YZ,),
        friction_types=[
            constants.FrictionType.CHEZY.value,
            constants.FrictionType.CHEZY_CONVEYANCE.value,
        ],
        message="Some values in cross_section_location.cross_section_friction_values are less than 1 while CHEZY friction is selected. This may cause nonsensical results.",
    )
]

# Checks for material
material_ref_tables = [models.Pipe, models.Culvert, models.Weir, models.Orifice]
conditions = [
    and_(
        table.material_id == models.Material.id,
        table.friction_value.is_(None),
        table.friction_type.is_(None),
    )
    for table in material_ref_tables
]
CHECKS += [
    # extend 22 for Materials.friction_value
    RangeCheck(
        error_code=1604,
        level=CheckLevel.WARNING,
        column=models.Material.friction_coefficient,
        filters=(models.Material.friction_type == constants.FrictionType.MANNING.value)
        & or_(*conditions),
        max_value=1,
        right_inclusive=False,  # 1 is not allowed
        message="material.friction_coefficient is not less than 1 while MANNING friction is selected. CHEZY friction will be used instead. In the future this will lead to an error.",
    ),
    RangeCheck(
        error_code=1605,
        level=CheckLevel.WARNING,
        column=models.Material.friction_coefficient,
        filters=(models.Material.friction_type == constants.FrictionType.CHEZY.value)
        & or_(*conditions),
        min_value=1,
        message="material.friction_coefficient is less than 1, while friction type is Chézy. This may lead to unexpected results. Did you mean to use friction type Manning?",
    ),
]


# Tags 2xxx
tables_with_tags = [model for model in models.DECLARED_MODELS if hasattr(model, "tags")]
CHECKS += [
    ListOfIntsCheck(
        error_code=2001 + i,
        level=CheckLevel.WARNING,
        column=table.tags,
    )
    for i, table in enumerate(tables_with_tags)
]


CHECKS += [
    TagsValidCheck(
        error_code=2007 + i,
        level=CheckLevel.WARNING,
        column=table.tags,
    )
    for i, table in enumerate(tables_with_tags)
]


# These checks are optional, depending on a command line argument
beta_features_check = []
beta_features_check += [
    BetaColumnsCheck(
        error_code=1300,
        column=col,
        level=CheckLevel.ERROR,
    )
    for col in BETA_COLUMNS
]
for pair in BETA_VALUES:
    beta_features_check += [
        BetaValuesCheck(
            error_code=1300,
            column=col,
            values=pair["values"],
            level=CheckLevel.ERROR,
        )
        for col in pair["columns"]
    ]


# columns that cannot be NULL in a valid schematisations
not_null_columns = [
    models.Channel.exchange_type,
    models.Channel.connection_node_id_start,
    models.Channel.connection_node_id_end,
    models.MeasureMap.weight,
    models.MeasureMap.measure_location_id,
    models.MeasureLocation.connection_node_id,
    models.MeasureLocation.measure_variable,
    models.MemoryControl.action_type,
    models.MemoryControl.action_value_1,
    models.MemoryControl.action_value_2,
    models.MemoryControl.target_type,
    models.MemoryControl.target_id,
    models.TableControl.action_table,
    models.TableControl.action_type,
    models.TableControl.target_type,
    models.CrossSectionLocation.channel_id,
    models.CrossSectionLocation.friction_type,
    models.CrossSectionLocation.reference_level,
    models.Culvert.connection_node_id_start,
    models.Culvert.connection_node_id_end,
    models.Culvert.invert_level_start,
    models.Culvert.invert_level_end,
    models.Orifice.connection_node_id_start,
    models.Orifice.connection_node_id_end,
    models.Orifice.crest_level,
    models.Orifice.crest_type,
    models.Pipe.connection_node_id_start,
    models.Pipe.connection_node_id_end,
    models.Pipe.exchange_type,
    models.Pipe.invert_level_end,
    models.Pipe.invert_level_start,
    models.Pump.connection_node_id,
    models.Pump.capacity,
    models.Pump.lower_stop_level,
    models.Pump.start_level,
    models.Pump.type_,
    models.PumpMap.pump_id,
    models.PumpMap.connection_node_id_end,
    models.Weir.connection_node_id_start,
    models.Weir.connection_node_id_end,
    models.Weir.crest_level,
    models.Weir.crest_type,
    models.Windshielding1D.channel_id,
    models.ModelSettings.node_open_water_detection,
]

# Foreign key check settings
fk_settings = [
    ForeignKeyCheckSetting(models.PumpMap.pump_id, models.Pump.id),
    ForeignKeyCheckSetting(
        models.MeasureMap.measure_location_id, models.MeasureLocation.id
    ),
    ForeignKeyCheckSetting(models.SurfaceMap.surface_id, models.Surface.id),
    ForeignKeyCheckSetting(
        models.Surface.surface_parameters_id, models.SurfaceParameters.id
    ),
    ForeignKeyCheckSetting(
        models.DryWeatherFlowMap.dry_weather_flow_id, models.DryWeatherFlow.id
    ),
    ForeignKeyCheckSetting(
        models.DryWeatherFlow.dry_weather_flow_distribution_id,
        models.DryWeatherFlowDistribution.id,
    ),
]
connection_node_fk = [
    models.Pump.connection_node_id,
    models.PumpMap.connection_node_id_end,
    models.MeasureLocation.connection_node_id,
    models.Channel.connection_node_id_start,
    models.Channel.connection_node_id_end,
    models.Culvert.connection_node_id_start,
    models.Culvert.connection_node_id_end,
    models.Orifice.connection_node_id_start,
    models.Orifice.connection_node_id_end,
    models.Pipe.connection_node_id_start,
    models.Pipe.connection_node_id_end,
    models.Weir.connection_node_id_start,
    models.Weir.connection_node_id_end,
    models.Lateral1D.connection_node_id,
    models.BoundaryCondition1D.connection_node_id,
    models.DryWeatherFlowMap.connection_node_id,
    models.SurfaceMap.connection_node_id,
]
fk_settings += [
    ForeignKeyCheckSetting(col, models.ConnectionNode.id) for col in connection_node_fk
]
channel_fk = [
    models.CrossSectionLocation.channel_id,
    models.Windshielding1D.channel_id,
    models.PotentialBreach.channel_id,
    models.ExchangeLine.channel_id,
]
fk_settings += [ForeignKeyCheckSetting(col, models.Channel.id) for col in channel_fk]
material_fk = [
    models.Pipe.material_id,
    models.Culvert.material_id,
    models.Weir.material_id,
    models.Orifice.material_id,
]
fk_settings += [ForeignKeyCheckSetting(col, models.Material.id) for col in material_fk]

control_tables = [models.MemoryControl, models.TableControl]
ref_tables = [
    models.Channel,
    models.Pipe,
    models.Orifice,
    models.Culvert,
    models.Weir,
    models.Pump,
]

fk_settings += [
    ForeignKeyCheckSetting(
        control_table.target_id,
        ref_table.id,
        control_table.target_type == ref_table.__tablename__,
    )
    for control_table in control_tables
    for ref_table in ref_tables
]

fk_settings += [
    ForeignKeyCheckSetting(
        models.MeasureMap.control_id,
        models.MemoryControl.id,
        models.MeasureMap.control_type == "memory",
    ),
    ForeignKeyCheckSetting(
        models.MeasureMap.control_id,
        models.TableControl.id,
        models.MeasureMap.control_type == "table",
    ),
]

level_map_fk_check = {
    "dry_weather_flow_map.connection_node_id": CheckLevel.WARNING,
    "dry_weather_flow_map.dry_weather_flow_id": CheckLevel.WARNING,
    "surface_map.connection_node_id": CheckLevel.WARNING,
    "surface_map.surface_id": CheckLevel.WARNING,
}

unique_columns = [models.BoundaryCondition1D.connection_node_id]


class Config:
    """Collection of checks

    Some checks are generated by a factory. These are usually very generic
    checks which apply to many columns, such as foreign keys."""

    def __init__(self, models, allow_beta_features=False):
        self.models = models
        self.checks = []
        self.allow_beta_features = allow_beta_features
        self.generate_checks()

    def generate_checks(self):
        self.checks = []
        # Error codes 1 to 9: factories
        for model in self.models:
            self.checks += generate_foreign_key_checks(
                model.__table__,
                error_code=1,
                fk_settings=fk_settings,
                custom_level_map=level_map_fk_check,
            )
            self.checks += generate_unique_checks(
                model.__table__, error_code=2, extra_unique_columns=unique_columns
            )
            self.checks += generate_not_null_checks(
                model.__table__, error_code=3, extra_not_null_columns=not_null_columns
            )
            self.checks += generate_type_checks(model.__table__, error_code=4)
            self.checks += generate_geometry_checks(
                model.__table__,
                custom_level_map={
                    "grid_refinement_line.geom": "warning",
                    "grid_refinement_area.geom": "warning",
                    "dem_average_area.geom": "warning",
                    "surface.geom": "warning",
                    "dry_weather_flow.geom": "warning",
                },
                error_code=5,
            )
            self.checks += generate_geometry_type_checks(
                model.__table__,
                error_code=6,
            )
            self.checks += generate_enum_checks(
                model.__table__,
                error_code=7,
                custom_level_map={
                    "pipe.sewerage_type": "INFO",
                    "pipe.material": "INFO",
                },
            )
            self.checks += [
                RangeCheck(
                    column=model.id,
                    error_code=8,
                    min_value=0,
                    max_value=2147483647,
                    message=f"{model.id.name} must be a positive signed 32-bit integer.",
                )
            ]
            self.checks += generate_epsg_geom_checks(model.__table__, error_code=9)
            self.checks += generate_epsg_raster_checks(
                model.__table__, RASTER_COLUMNS, error_code=10
            )

        self.checks += CHECKS
        if not self.allow_beta_features:
            self.checks += beta_features_check

    def iter_checks(self, level=CheckLevel.ERROR, ignore_checks=None):
        """Iterate over checks with at least 'level'"""
        level = CheckLevel.get(level)  # normalize
        for check in self.checks:
            if check.is_beta_check and not self.allow_beta_features:
                continue
            if check.level >= level:
                if ignore_checks:
                    if not ignore_checks.match(str(check.error_code).zfill(4)):
                        yield check
                else:
                    yield check
