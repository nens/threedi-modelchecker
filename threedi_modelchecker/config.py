from .checks.base import BaseCheck
from .checks.base import EnumCheck
from .checks.base import FileExistsCheck
from .checks.base import ForeignKeyCheck
from .checks.base import GeneralCheck
from .checks.base import GeometryCheck
from .checks.base import GeometryTypeCheck
from .checks.base import QueryCheck
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
from sqlalchemy import cast
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy.orm import Query
from typing import List


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
    GeneralCheck(
        column=models.CrossSectionLocation.friction_value,
        criterion_valid=models.CrossSectionLocation.friction_value >= 0,
    ),
    GeneralCheck(
        column=models.CrossSectionLocation.friction_value,
        criterion_invalid=(
            models.CrossSectionLocation.friction_type == constants.FrictionType.MANNING
        )
        & (models.CrossSectionLocation.friction_value >= 1),
    ),
    GeneralCheck(
        column=models.Culvert.friction_value,       
        criterion_valid=models.Culvert.friction_value >= 0,
    ),
    GeneralCheck(
        column=models.Culvert.friction_value,
        criterion_invalid=(
            models.Culvert.friction_type == constants.FrictionType.MANNING
        )
        & (models.Culvert.friction_value >= 1),
    ),
    GeneralCheck(
        column=models.GroundWater.phreatic_storage_capacity,
        criterion_invalid=(
            (models.GroundWater.global_settings != None)
            & (
                (models.GroundWater.phreatic_storage_capacity < 0)
                | (models.GroundWater.phreatic_storage_capacity > 1)
            )
        ),
    ),
    GeneralCheck(
        column=models.ImperviousSurface.area, # TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        criterion_valid=models.ImperviousSurface.area >= 0,
    ),
    GeneralCheck(
        column=models.ImperviousSurface.dry_weather_flow,  # # TODO: warning, alleen checken als dry_weather_flow aangeroepen wordt 
        criterion_valid=models.ImperviousSurface.dry_weather_flow >= 0,
    ),
    GeneralCheck(
        column=models.ImperviousSurfaceMap.percentage,  # TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        criterion_valid=models.ImperviousSurfaceMap.percentage >= 0,
    ),
    GeneralCheck(  # TODO: Error, alleen checken als interflow aangeroepen wordt in global settings
        column=models.Interflow.porosity,
        criterion_valid=and_(
            models.Interflow.porosity >= 0,
            models.Interflow.porosity <= 1,
        ),
    ),
    GeneralCheck(
        column=models.Interflow.impervious_layer_elevation,  # TODO: Error, alleen checken als interflow aangeroepen wordt in global settings
        criterion_valid=models.Interflow.impervious_layer_elevation >= 0,
    ),
    GeneralCheck(
        column=models.Orifice.discharge_coefficient_negative, # TODO: Error
        criterion_valid=models.Orifice.discharge_coefficient_negative >= 0,
    ),
    GeneralCheck(
        column=models.Orifice.discharge_coefficient_positive, # TODO: Error
        criterion_valid=models.Orifice.discharge_coefficient_positive >= 0,
    ),
    GeneralCheck(
        column=models.Orifice.friction_value, # TODO: Error, alleen als type =3
        criterion_valid=models.Orifice.friction_value >= 0,  # friction_type=2 ook kleiner zijn dan 1 
    ),
    GeneralCheck(
        column=models.Pipe.dist_calc_points, # TODO: Error
        criterion_valid=models.Pipe.dist_calc_points > 0,
    ),
    GeneralCheck(
        column=models.Pipe.friction_value, # TODO: Error
        criterion_valid=models.Pipe.friction_value >= 0,
    ),
    GeneralCheck(
        column=models.Pumpstation.upper_stop_level, # TODO: Error
        criterion_valid=and_(
            models.Pumpstation.upper_stop_level > models.Pumpstation.lower_stop_level,
            models.Pumpstation.upper_stop_level > models.Pumpstation.start_level,
        )
    ),
    GeneralCheck(
        column=models.Pumpstation.lower_stop_level, # TODO: Error 
        criterion_valid=and_(
            models.Pumpstation.lower_stop_level < models.Pumpstation.start_level,
            models.Pumpstation.lower_stop_level < models.Pumpstation.upper_stop_level,
        )
    ),

    #TODO: toevoegen: check op bottom level van connection node, moet groter zijn, anders error

    GeneralCheck( # TODO: Error
        column=models.Pumpstation.start_level, 
        criterion_valid=and_(
            models.Pumpstation.start_level > models.Pumpstation.lower_stop_level,
            models.Pumpstation.start_level < models.Pumpstation.upper_stop_level,
        )
    ),
    GeneralCheck( # TODO: Error
        column=models.Pumpstation.capacity,
        criterion_valid=models.Pumpstation.capacity >= 0,
    ),

    # TODO: Toevoegen, als models.Pumpstation.capacity=0 Warning geven

    GeneralCheck( # TODO: Error
        column=models.SimpleInfiltration.infiltration_rate,
        criterion_valid=models.SimpleInfiltration.infiltration_rate >= 0,
    ),
    GeneralCheck( # TODO: warning, alleen checken als dry_weather_flow aangeroepen wordt 
        column=models.Surface.nr_of_inhabitants,
        criterion_valid=models.Surface.nr_of_inhabitants >= 0,
    ),
    GeneralCheck( # TODO: warning, alleen checken als dry_weather_flow aangeroepen wordt 
        column=models.Surface.dry_weather_flow,
        criterion_valid=models.Surface.dry_weather_flow >= 0,
    ),
    GeneralCheck( # TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.Surface.area,
        criterion_valid=models.Surface.area >= 0,
    ),
    GeneralCheck( # TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.SurfaceMap.percentage,
        criterion_valid=and_(
            models.SurfaceMap.percentage >= 0,
            models.SurfaceMap.percentage <= 100, #TODO: Warning van maken. error alleen bij < 0
        ),
    ),
    GeneralCheck( # TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.SurfaceParameter.outflow_delay,
        criterion_valid=models.SurfaceParameter.outflow_delay >= 0,
    ),
    GeneralCheck( # TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.SurfaceParameter.max_infiltration_capacity,
        criterion_valid=models.SurfaceParameter.max_infiltration_capacity >= 0,
    ),
    GeneralCheck(# TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.SurfaceParameter.min_infiltration_capacity,
        criterion_valid=models.SurfaceParameter.min_infiltration_capacity >= 0,
    ),
    GeneralCheck(# TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.SurfaceParameter.infiltration_decay_constant,
        criterion_valid=models.SurfaceParameter.infiltration_decay_constant >= 0,
    ),
    GeneralCheck(# TODO: Error, alleen checken als 0D inflow aangeroepen wordt in global settings
        column=models.SurfaceParameter.infiltration_recovery_constant,
        criterion_valid=models.SurfaceParameter.infiltration_recovery_constant >= 0,
    ),
    GeneralCheck(# TODO: Error
        column=models.Weir.discharge_coefficient_negative,
        criterion_valid=models.Weir.discharge_coefficient_negative >= 0,
    ),
    GeneralCheck(# TODO: Error
        column=models.Weir.discharge_coefficient_positive,
        criterion_valid=models.Weir.discharge_coefficient_positive >= 0,
    ),
    GeneralCheck(# TODO: Error, alleen bij type 3 weirs, bij type 4 hoeft het niet gecheckt te worden
        column=models.Weir.friction_value,
        criterion_valid=models.Weir.friction_value >= 0, #friction_type=2 ook kleiner zijn dan 1
    ),

    GeneralCheck( #TODO: zou in de api checks moeten zitten
        column=models.GlobalSetting.maximum_sim_time_step,
        criterion_valid=models.GlobalSetting.maximum_sim_time_step >= models.GlobalSetting.sim_time_step,
    ),
    GeneralCheck( #TODO: zou in de api checks moeten zitten
        column=models.GlobalSetting.sim_time_step,
        criterion_valid=models.GlobalSetting.sim_time_step >= models.GlobalSetting.minimum_sim_time_step,
    ),
]

OTHER_CHECKS: List[BaseCheck] = [ 
    BankLevelCheck(),
    CrossSectionShapeCheck(),
    # 1d boundary conditions cannot be connected to a pumpstation
    GeneralCheck( #TODO: error
        column=models.BoundaryCondition1D.connection_node_id,
        criterion_invalid=or_(
            models.BoundaryCondition1D.connection_node_id == models.Pumpstation.connection_node_start_id,
            models.BoundaryCondition1D.connection_node_id == models.Pumpstation.connection_node_end_id,
        )
    ),
    Use0DFlowCheck(),
    OpenChannelsWithNestedNewton(),
    ConnectionNodesDistance(minimum_distance=0.01),
]


CONDITIONAL_CHECKS = [
    QueryCheck(
        column=models.ConnectionNode.storage_area,
        invalid=Query(models.ConnectionNode).join(
            models.Manhole
        ).filter(
            models.ConnectionNode.storage_area < 0
        ),
        message="WARNING: The ConnectionNode.storage_area should be >= 0 "
                "when the ConnectionNode is a Manhole"
    ),
    QueryCheck(
        column=models.CrossSectionLocation.reference_level,
        invalid=Query(models.CrossSectionLocation).filter(
            models.CrossSectionLocation.bank_level != None,
            models.CrossSectionLocation.reference_level >= models.CrossSectionLocation.bank_level
        ),
        message="CrossSectionLocation.reference_level should be below the CrossSectionLocation.bank_level"
                "when CrossSectionLocation.bank_level is not null"
    ),
    QueryCheck(
        column=models.GlobalSetting.dem_obstacle_height,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.dem_obstacle_height <= 0,
            models.GlobalSetting.dem_obstacle_detection == True
        ),
        message="GlobalSetting.dem_obstacle_height should be larger than 0 when "
                "GlobalSetting.dem_obstacle_detection == True" #TODO error
    ),
    QueryCheck( #TODO: error, maar alleen checken als groundwater ingevuld is in the global settings
        column=models.GroundWater.equilibrium_infiltration_rate_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.equilibrium_infiltration_rate_type == None,
            models.GroundWater.equilibrium_infiltration_rate_file != None
        ),
        message="The field GroundWater.equilibrium_infiltration_rate_type should be filled, when using "
                "GroundWater.equilibrium_infiltration_rate_file."
    ),
    QueryCheck( #TODO: error, maar alleen checken als groundwater ingevuld is in the global settings
        column=models.GroundWater.infiltration_decay_period_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.infiltration_decay_period_type == None,
            models.GroundWater.infiltration_decay_period_type != None
        ),
        message="The field GroundWater.infiltration_decay_period_type should be filled, when using"
                "GroundWater.infiltration_decay_period_type."
    ),
    QueryCheck(#TODO: error, maar alleen checken als groundwater ingevuld is in the global settings
        column=models.GroundWater.groundwater_hydro_connectivity_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.groundwater_hydro_connectivity_type == None,
            models.GroundWater.groundwater_hydro_connectivity_file != None
        ),
        message="The field GroundWater.groundwater_hydro_connectivity_type should be filled, when using "
                "GroundWater.groundwater_hydro_connectivity_file is not null"
    ),
    QueryCheck(#TODO: error, maar alleen checken als groundwater ingevuld is in the global settings
        column=models.GroundWater.groundwater_impervious_layer_level_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.groundwater_impervious_layer_level_type == None,
            models.GroundWater.groundwater_impervious_layer_level_file != None
        ),
        message="The field GroundWater.groundwater_impervious_layer_level_type should be filled, when using"
                "when GroundWater.groundwater_impervious_layer_level_file"
    ),
    QueryCheck(#TODO: error, maar alleen checken als groundwater ingevuld is in the global settings
        column=models.GroundWater.initial_infiltration_rate_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.initial_infiltration_rate_type == None,
            models.GroundWater.initial_infiltration_rate_file != None
        ),
        message="The field GroundWater.initial_infiltration_rate_type should be filled, when using "
                "GroundWater.initial_infiltration_rate_file"
    ),
    QueryCheck(#TODO: error, maar alleen checken als groundwater ingevuld is in the global settings
        column=models.GroundWater.phreatic_storage_capacity_type,
        invalid=Query(models.GroundWater).filter(
            models.GroundWater.initial_infiltration_rate_type == None,
            models.GroundWater.initial_infiltration_rate_file != None
        ),
        message="The field GroundWater.phreatic_storage_capacity_type should be filled, when using "
                "GroundWater.phreatic_storage_capacity_file."
    ),
    QueryCheck(#TODO: error, maar alleen checken als interflow ingevuld is in the global settings
        column=models.Interflow.porosity,
        invalid=Query(models.Interflow).filter(
            models.Interflow.porosity == None,
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW
        ),
        message=f"The field Interflow.porosity should be filled, when "
                f"Interflow.interflow_type != {constants.InterflowType.NO_INTERLFOW}"
    ),
    QueryCheck(#TODO: error, maar alleen checken als interflow ingevuld is in the global settings, thickness moet groter dan 0 zijn
        column=models.Interflow.porosity_layer_thickness,
        invalid=Query(models.Interflow).filter(
            models.Interflow.porosity_layer_thickness == None,
            models.Interflow.interflow_type in [
                constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY,
                constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY,
            ]
        ),
        message=f"Interflow.porosity_layer_thickness should be filled and >0 in case "
                f"Interflow.interflow_type is "
                f"{constants.InterflowType.LOCAL_DEEPEST_POINT_SCALED_POROSITY} or "
                f"{constants.InterflowType.GLOBAL_DEEPEST_POINT_SCALED_POROSITY}"
    ),
    QueryCheck( #TODO: error
        column=models.Interflow.impervious_layer_elevation,
        invalid=Query(models.Interflow).filter(
            models.Interflow.impervious_layer_elevation == None,
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW
        ),
        message=f"Interflow.impervious_layer_elevation cannot be null when "
                f"Interflow.interflow_type is not {constants.InterflowType.NO_INTERLFOW}"
    ),
    QueryCheck(#TODO: error, maar alleen checken als interflow ingevuld is in the global settings
        column=models.Interflow.hydraulic_conductivity,
        invalid=Query(models.Interflow).filter(
            or_(
                models.Interflow.hydraulic_conductivity == None,
                models.Interflow.hydraulic_conductivity_file == None,
            ),
            models.Interflow.interflow_type != constants.InterflowType.NO_INTERLFOW
        ),
        message=f"Interflow.hydraulic_conductivity cannot be null or "
                f"Interflow.hydraulic_conductivity_file cannot be null when "
                f"Interflow.interflow_type != {constants.InterflowType.NO_INTERLFOW}"
    ),
    QueryCheck(#TODO: ERROR
        column=models.Channel.calculation_type,
        invalid=Query(models.Channel).filter(
            models.Channel.calculation_type.in_([
                constants.CalculationType.EMBEDDED,
                constants.CalculationType.CONNECTED,
                constants.CalculationType.DOUBLE_CONNECTED
            ]),
            models.GlobalSetting.dem_file == None
        ),
        message=f"Channel.calculation_type cannot be "
                f"{constants.CalculationType.EMBEDDED} or"
                f"{constants.CalculationType.CONNECTED} or "
                f"{constants.CalculationType.DOUBLE_CONNECTED} when "
                f"GlobalSetting.dem_file is null"
    ),
    QueryCheck(#TODO: Warning& toevoegen van een "future warning  "We will stop correcting this in the future, this constraint will be mandatory in the database"
        column=models.Pumpstation.lower_stop_level,
        invalid=Query(models.Pumpstation).join(
            models.ConnectionNode,
            models.Pumpstation.connection_node_start_id == models.ConnectionNode.id
        ).join(
            models.Manhole
        ).filter(
            models.Pumpstation.type_ == constants.PumpType.SUCTION_SIDE,
            models.Pumpstation.lower_stop_level <= models.Manhole.bottom_level,
        ),
        message="Pumpstation.lower_stop_level should be higher than "
                "Manhole.bottom_level. Computational core will use Manhole.bottom_level as lower_stop_level."
    ),
    QueryCheck(#TODO: Warning& toevoegen van een "future warning  "We will stop correcting this in the future, this constraint will be mandatory in the database"
        column=models.Pumpstation.lower_stop_level,
        invalid=Query(models.Pumpstation).join(
            models.ConnectionNode,
            models.Pumpstation.connection_node_end_id == models.ConnectionNode.id
        ).join(
            models.Manhole
        ).filter(
            models.Pumpstation.type_ == constants.PumpType.DELIVERY_SIDE,
            models.Pumpstation.lower_stop_level <= models.Manhole.bottom_level,
        ),
        message="Pumpstation.lower_stop_level should be higher than "
                "Manhole.bottom_level.  Computational core will use Manhole.bottom_level as lower_stop_level."
    ),
    QueryCheck(#TODO: Warning& toevoegen van een "future warning  "We will stop correcting this in the future, this constraint will be mandatory in the database"
        column=models.Pipe.invert_level_end_point,
        invalid=Query(models.Pipe).join(
            models.ConnectionNode,
            models.Pipe.connection_node_end_id == models.ConnectionNode.id
        ).join(
            models.Manhole
        ).filter(
            models.Pipe.invert_level_end_point < models.Manhole.bottom_level,
        ),
        message="Pipe.invert_level_end_point should be higher than or equal to "
                "Manhole.bottom_level. Computational core will use Manhole.bottom_level as Pipe.invert_level_end_point."
    ),
    QueryCheck(#TODO: Warning& toevoegen van een "future warning  "We will stop correcting this in the future, this constraint will be mandatory in the database"
        column=models.Pipe.invert_level_start_point,
        invalid=Query(models.Pipe).join(
            models.ConnectionNode,
            models.Pipe.connection_node_start_id == models.ConnectionNode.id
        ).join(
            models.Manhole
        ).filter(
            models.Pipe.invert_level_start_point < models.Manhole.bottom_level,
        ),
        message="Pipe.invert_level_start_point should be higher than or equal to "
                "Manhole.bottom_level.  Computational core will use Manhole.bottom_level as Pipe.invert_level_start_point."
    ),
    QueryCheck(#TODO: Warning& toevoegen van een "future warning  "We will stop correcting this in the future, this constraint will be mandatory in the database"
        column=models.Manhole.bottom_level,
        invalid=Query(models.Manhole).filter(
            models.Manhole.drain_level < models.Manhole.bottom_level,
            models.Manhole.calculation_type == constants.CalculationTypeNode.CONNECTED
        ),
        message="Manhole.drain_level >= Manhole.bottom_level when "
                "Manhole.calculation_type is CONNECTED.  Computational core will use Manhole.bottom_level as Manhole.drain_level."
    ),
    QueryCheck(#TODO als er geen DEM is en manhole_storage_area is ingevuld, alleen dan is dit een warning, anders info melding. Future warning "In case of using sub-basins this constraint becomes mandatory. "
        column=models.Manhole.drain_level,
        invalid=Query(models.Manhole).filter(
            models.Manhole.calculation_type == constants.CalculationTypeNode.CONNECTED,
            models.Manhole.drain_level == None
        ),
        message="Manhole.drain_level cannot be null when Manhole.calculation_type is "
                "CONNECTED"
    ),
    QueryCheck(#TODO mag volgens ons weg, wordt via api settings gedaan
        column=models.GlobalSetting.maximum_sim_time_step,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.timestep_plus == True,
            models.GlobalSetting.maximum_sim_time_step == None
        ),
        message="GlobalSettings.maximum_sim_time_step cannot be null when "
                "GlobalSettings.timestep_plus is True"
    ),
    QueryCheck(#TODO Error
        column=models.GlobalSetting.use_1d_flow,
        invalid=Query(models.GlobalSetting).filter(
            models.GlobalSetting.use_1d_flow == False,
            Query(func.count(models.ConnectionNode.id) > 0).label("1d_count")
        ),
        message="GlobalSettings.use_1d_flow must be set to True when there are 1D "
                "elements in the model"
    ),
    QueryCheck(# TODO Warning 
        column=models.Channel.id,
        invalid=Query(models.Channel).filter(
            geo_func.ST_Length(
                geo_func.ST_Transform(
                    models.Channel.the_geom,
                    Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code")
                )
            ) < 0.05
        ),
        message="Length of the line geometry is very short. Consider extending individual geometries to 1.0 m"
    ),
    QueryCheck(# TODO Warning 
        column=models.Culvert.id,
        invalid=Query(models.Culvert).filter(
            geo_func.ST_Length(
                geo_func.ST_Transform(
                    models.Culvert.the_geom,
                    Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code")
                )
            ) < 0.05
        ),
        message="Length of the line geometry is very short. Consider extending individual geometries to 1.0 m"
    ),
    ConnectionNodesLength( #TO DO zie foutmelding hierover bij culverts, we willen een check distance en een advies distance
        column=models.Pipe.id,
        start_node=models.Pipe.connection_node_start,
        end_node=models.Pipe.connection_node_end,
        min_distance=0.05
    ),
    ConnectionNodesLength(#TODO Alleen checken voor kcu=3 +zie foutmelding hierover bij culverts, we willen een check distance en een advies distance
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05
    ),
    ConnectionNodesLength(#TODO Alleen checken voor kcu=3 +zie foutmelding hierover bij culverts, we willen een check distance en een advies distance
        column=models.Orifice.id,
        start_node=models.Orifice.connection_node_start,
        end_node=models.Orifice.connection_node_end,
        min_distance=0.05
    ),
    QueryCheck(#TODO Warning
        column=models.ConnectionNode.id,
        invalid=Query(models.ConnectionNode).filter(
            models.ConnectionNode.id.notin_(
                Query(models.Manhole.connection_node_id).union_all(
                    Query(models.Pipe.connection_node_start_id),
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
                    Query(models.Orifice.connection_node_end_id)
                )
            )
        ),
        message="This is an individual, ConnectionNode. Possibly it should be connected to either a manhole, pipe, "
                "channel, culvert, weir, pumpstation or orifice"
    ),
    QueryCheck(#TODO Warning & toevoegen combinatie van pipes, met weir, met orrifice and met culverts
        column=models.Pipe.id,
        invalid=Query(models.Pipe).join(
            models.ConnectionNode,
            models.Pipe.connection_node_start_id == models.ConnectionNode.id
        ).filter(
            models.Pipe.calculation_type == constants.PipeCalculationType.ISOLATED,
            models.ConnectionNode.storage_area.is_(None)
        ).union(
            Query(models.Pipe).join(
                models.ConnectionNode,
                models.Pipe.connection_node_end_id == models.ConnectionNode.id
            ).filter(
                models.Pipe.calculation_type == constants.PipeCalculationType.ISOLATED,
                models.ConnectionNode.storage_area.is_(None)
            )
        ),
        message="It can be beneficial for the computational stability to add storage to a connection_node in case of connecting two isolated pipes."
    ),
    QueryCheck(#TODO Error
        column=models.NumericalSettings.convergence_eps,
        invalid=Query(models.NumericalSettings).filter(
            models.NumericalSettings.convergence_eps <= 0
        ),
        message="NumericalSettings.convergence_eps must be larger than 0"
    ),
    QueryCheck(#TODO Error
        column=models.NumericalSettings.convergence_cg,
        invalid=Query(models.NumericalSettings).filter(
            models.NumericalSettings.convergence_cg <= 0
        ),
        message="NumericalSettings.convergence_cg must be larger than 0"
    ),
    QueryCheck(#TODO Error
        column=models.NumericalSettings.general_numerical_threshold,
        invalid=Query(models.NumericalSettings).filter(
            models.NumericalSettings.general_numerical_threshold <= 0
        ),
        message="NumericalSettings.general_numerical_threshold must be larger than 0"
    ),
    QueryCheck(#TODO Error
        column=models.NumericalSettings.flow_direction_threshold,
        invalid=Query(models.NumericalSettings).filter(
            models.NumericalSettings.flow_direction_threshold <= 0
        ),
        message="NumericalSettings.flow_direction_threshold must be larger than 0"
    ),
    QueryCheck(#TODO Warning
        column=models.NumericalSettings.use_of_nested_newton,
        invalid=Query(models.NumericalSettings).filter(
            models.NumericalSettings.use_of_nested_newton == 0,
            or_(
                Query(func.count(models.Pipe.id) > 0).label("pipes"),
                Query(func.count(models.Culvert.id) > 0).label("culverts"),
                Query(func.count(models.Orifice.id) > 0).label("orifices")
            )
        ),
        message="NumericalSettings.use_of_nested_newton is turned off, this in "
                "combination with pipes, culverts or orifices in the model can "
                "increase your computational cost. Please consider turning this on "
                "NumericalSettings.use_of_nested_newton or removing the pipes, "
                "culverts and orifices."
    ),
]


FILE_EXISTS_CHECKS = [
    FileExistsCheck(column=models.GlobalSetting.dem_file),
    FileExistsCheck(column=models.GlobalSetting.frict_coef_file),
    FileExistsCheck(column=models.GlobalSetting.interception_file),
    FileExistsCheck(
        column=models.Interflow.porosity_file,
        filters=[models.Interflow.global_settings != None],
    ),
    FileExistsCheck(
        column=models.Interflow.hydraulic_conductivity_file,
        filters=[models.Interflow.global_settings != None],
    ),
    FileExistsCheck(
        column=models.SimpleInfiltration.infiltration_rate_file,
        filters=[models.SimpleInfiltration.global_settings != None],
    ),
    FileExistsCheck(
        column=models.SimpleInfiltration.max_infiltration_capacity_file,
        filters=[models.SimpleInfiltration.global_settings != None],
    ),
    FileExistsCheck(
        column=models.GroundWater.groundwater_hydro_connectivity_file,
        filters=[models.GroundWater.global_settings != None],
    ),
    FileExistsCheck(
        column=models.GroundWater.phreatic_storage_capacity_file,
        filters=[models.GroundWater.global_settings != None],
    ),
    FileExistsCheck(
        column=models.GroundWater.equilibrium_infiltration_rate_file,
        filters=[models.GroundWater.global_settings != None],
    ),
    FileExistsCheck(
        column=models.GroundWater.initial_infiltration_rate_file,
        filters=[models.GroundWater.global_settings != None],
    ),
    FileExistsCheck(
        column=models.GroundWater.infiltration_decay_period_file,
        filters=[models.GroundWater.global_settings != None],
    ),
    FileExistsCheck(
        column=models.GroundWater.groundwater_hydro_connectivity_file,
        filters=[models.GroundWater.global_settings != None],
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
        for model in self.models: #TODO splitsing tussen warning en errors ? Afhankelijk van hoeveel werk
            FOREIGN_KEY_CHECKS += generate_foreign_key_checks(model.__table__)
            UNIQUE_CHECKS += generate_unique_checks(model.__table__)
            NOT_NULL_CHECKS += generate_not_null_checks(model.__table__)
            INVALID_TYPE_CHECKS += generate_type_checks(model.__table__)
            INVALID_GEOMETRY_CHECKS += generate_geometry_checks(model.__table__)
            INVALID_GEOMETRY_TYPE_CHECKS += generate_geometry_type_checks(model.__table__)
            INVALID_ENUM_CHECKS += generate_enum_checks(model.__table__)

        self.checks += FOREIGN_KEY_CHECKS
        self.checks += UNIQUE_CHECKS
        self.checks += NOT_NULL_CHECKS
        self.checks += INVALID_TYPE_CHECKS
        self.checks += INVALID_GEOMETRY_CHECKS
        self.checks += INVALID_GEOMETRY_TYPE_CHECKS
        self.checks += INVALID_ENUM_CHECKS
        self.checks += OTHER_CHECKS
        self.checks += TIMESERIES_CHECKS #TODO: Deze moet weg, en naar template/event validatie
        self.checks += RANGE_CHECKS
        self.checks += CONDITIONAL_CHECKS
        self.checks += FILE_EXISTS_CHECKS
        return None
