from sqlalchemy import or_

from .checks.base import ConditionalCheck
from .checks.base import NotNullCheck
from .checks.base import RangeCheck
from .checks.factories import generate_enum_checks
from .checks.factories import generate_foreign_key_checks
from .checks.factories import generate_geometry_checks
from .checks.factories import generate_geometry_type_checks
from .checks.factories import generate_type_checks
from .checks.factories import generate_unique_checks
from .checks.other import BankLevelCheck
from .checks.other import TimeseriesCheck
from .threedi_model import models
from .threedi_model.models import constants

FOREIGN_KEY_CHECKS = []
UNIQUE_CHECKS = []
INVALID_TYPE_CHECKS = []
INVALID_GEOMETRY_CHECKS = []
INVALID_GEOMETRY_TYPE_CHECKS = []
INVALID_ENUM_CHECKS = []

TIMESERIES_CHECKS = [
    TimeseriesCheck(models.BoundaryCondition1D.timeseries),
    TimeseriesCheck(models.BoundaryConditions2D.timeseries),
    TimeseriesCheck(models.Lateral1d.timeseries),
    TimeseriesCheck(models.Lateral2D.timeseries),
]

RANGE_CHECKS = [
    RangeCheck(column=models.CrossSectionLocation.friction_value, lower_limit=0),
    RangeCheck(column=models.Culvert.friction_value, lower_limit=0),
    RangeCheck(column=models.GroundWater.phreatic_storage_capacity, lower_limit=0, upper_limit=1),
    RangeCheck(column=models.ImperviousSurface.area, lower_limit=0),
    RangeCheck(column=models.ImperviousSurface.dry_weather_flow, lower_limit=0),
    RangeCheck(column=models.ImperviousSurfaceMap.percentage, lower_limit=0),
    RangeCheck(column=models.Interflow.porosity, lower_limit=0, upper_limit=1),
    RangeCheck(column=models.Interflow.impervious_layer_elevation, lower_limit=0),
    RangeCheck(column=models.Orifice.discharge_coefficient_negative, lower_limit=0),
    RangeCheck(column=models.Orifice.discharge_coefficient_positive, lower_limit=0),
    RangeCheck(column=models.Orifice.friction_value, lower_limit=0),
    RangeCheck(column=models.Pipe.dist_calc_points, lower_limit=0),
    RangeCheck(column=models.Pipe.friction_value, lower_limit=0),
    RangeCheck(column=models.Pumpstation.upper_stop_level, lower_limit=models.Pumpstation.lower_stop_level),
    RangeCheck(column=models.Pumpstation.upper_stop_level, lower_limit=models.Pumpstation.start_level),
    RangeCheck(column=models.Pumpstation.lower_stop_level, upper_limit=models.Pumpstation.start_level),
    RangeCheck(column=models.Pumpstation.lower_stop_level, upper_limit=models.Pumpstation.upper_stop_level),
    RangeCheck(column=models.Pumpstation.start_level, lower_limit=models.Pumpstation.lower_stop_level),
    RangeCheck(column=models.Pumpstation.start_level, upper_limit=models.Pumpstation.upper_stop_level),
    RangeCheck(column=models.Pumpstation.capacity, lower_limit=0),
    RangeCheck(column=models.SimpleInfiltration.infiltration_rate, lower_limit=0),
    RangeCheck(column=models.Surface.nr_of_inhabitants, lower_limit=0),
    RangeCheck(column=models.Surface.area, lower_limit=0),
    RangeCheck(column=models.SurfaceMap.percentage, lower_limit=0, upper_limit=100),
    RangeCheck(column=models.SurfaceParameter.max_infiltration_capacity, lower_limit=0),
    RangeCheck(column=models.SurfaceParameter.min_infiltration_capacity, lower_limit=0),
    RangeCheck(column=models.SurfaceParameter.infiltration_decay_constant, lower_limit=0),
    RangeCheck(column=models.SurfaceParameter.infiltration_recovery_constant, lower_limit=0),
    RangeCheck(column=models.SurfaceParameter.outflow_delay, lower_limit=0),
    RangeCheck(column=models.Weir.discharge_coefficient_negative, lower_limit=0),
    RangeCheck(column=models.Weir.discharge_coefficient_negative, lower_limit=0),
    RangeCheck(column=models.Weir.friction_value, lower_limit=0),
]

OTHER_CHECKS = [
    BankLevelCheck(),
    # CrossSectionShapeCheck(),
]

CONDITIONAL_CHECKS = [
    # If a connection_node is a manhole, then storage_area > 0
    ConditionalCheck(
        criterion=(models.ConnectionNode.id == models.Manhole.connection_node_id),
        check=RangeCheck(
            column=models.ConnectionNode.storage_area,
            lower_limit=0
        )
    ),
    ConditionalCheck(
            criterion=(models.CrossSectionLocation.bank_level != None),
            check=RangeCheck(
                column=models.CrossSectionLocation.reference_level,
                upper_limit=models.CrossSectionLocation.bank_level
            )
        ),
    ConditionalCheck(
        criterion=(models.GlobalSetting.timestep_plus == True),
        check=NotNullCheck(
            column=models.GlobalSetting.maximum_sim_time_step,
        )
    ),
    ConditionalCheck(
        criterion=or_(
            models.GlobalSetting.initial_groundwater_level_file != None,
            models.GlobalSetting.initial_groundwater_level != None
        ),
        check=NotNullCheck(
            column=models.GlobalSetting.initial_groundwater_level_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GlobalSetting.initial_waterlevel_file != None,
        check=NotNullCheck(
            column=models.GlobalSetting.water_level_ini_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GlobalSetting.initial_waterlevel_file != None,
        check=NotNullCheck(
            column=models.GlobalSetting.water_level_ini_type,
        )
    ),
    # ConditionalCheck(
    #     criterion=models.GlobalSetting.use_0d_inflow == 1,
    #     check=NotNullCheck(
    #         column=models.GlobalSetting., # v2_impervious_surface
    #     )
    # ),
    ConditionalCheck(
        criterion=models.GlobalSetting.dem_obstacle_detection == True,
        check=RangeCheck(
            column=models.GlobalSetting.dem_obstacle_height,
            lower_limit=0
        )
    ),
    ConditionalCheck(
        criterion=models.GroundWater.equilibrium_infiltration_rate_file != None,
        check=NotNullCheck(
            column=models.GroundWater.equilibrium_infiltration_rate_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GroundWater.infiltration_decay_period_file != None,
        check=NotNullCheck(
            column=models.GroundWater.infiltration_decay_period_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GroundWater.groundwater_hydro_connectivity_file != None,
        check=NotNullCheck(
            column=models.GroundWater.groundwater_hydro_connectivity_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GroundWater.groundwater_impervious_layer_level_file != None,
        check=NotNullCheck(
            column=models.GroundWater.groundwater_impervious_layer_level_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GroundWater.initial_infiltration_rate_file != None,
        check=NotNullCheck(
            column=models.GroundWater.initial_infiltration_rate_type,
        )
    ),
    ConditionalCheck(
        criterion=models.GroundWater.phreatic_storage_capacity_file != None,
        check=NotNullCheck(
            column=models.GroundWater.phreatic_storage_capacity_type,
        )
    ),
    ConditionalCheck(
        criterion=models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        check=NotNullCheck(
            column=models.Interflow.porosity,
        )
    ),
    ConditionalCheck(
        criterion=models.Interflow.interflow_type in [
            constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY,
            constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY,
        ],
        check=NotNullCheck(
            column=models.Interflow.porosity_layer_thickness,
        )
    ),
    ConditionalCheck(
        criterion=models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW,
        check=NotNullCheck(
            column=models.Interflow.impervious_layer_elevation,
        )
    ),


]


ALL_CHECKS = []


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
        INVALID_TYPE_CHECKS = []
        INVALID_GEOMETRY_CHECKS = []
        INVALID_GEOMETRY_TYPE_CHECKS = []
        INVALID_ENUM_CHECKS = []
        # Call the check factories:
        for model in self.models:
            FOREIGN_KEY_CHECKS += generate_foreign_key_checks(model.__table__)
            UNIQUE_CHECKS += generate_unique_checks(model.__table__)
            INVALID_TYPE_CHECKS += generate_type_checks(model.__table__)
            INVALID_GEOMETRY_CHECKS += generate_geometry_checks(model.__table__)
            INVALID_GEOMETRY_TYPE_CHECKS += generate_geometry_type_checks(model.__table__)
            INVALID_ENUM_CHECKS += generate_enum_checks(model.__table__)

        self.checks += FOREIGN_KEY_CHECKS
        self.checks += UNIQUE_CHECKS
        self.checks += INVALID_TYPE_CHECKS
        self.checks += INVALID_GEOMETRY_CHECKS
        self.checks += INVALID_GEOMETRY_TYPE_CHECKS
        self.checks += INVALID_ENUM_CHECKS
        self.checks += OTHER_CHECKS
        self.checks += TIMESERIES_CHECKS
        self.checks += RANGE_CHECKS
        self.checks += CONDITIONAL_CHECKS
        return None
