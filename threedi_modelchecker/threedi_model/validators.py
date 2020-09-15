from datetime import datetime, date
from typing import Optional

from geoalchemy2.types import Geometry
from geoalchemy2.elements import WKBElement
from pydantic import BaseModel, constr, validator

from . import constants, models
from .constants import Material, CalculationType


class ORMBaseModel(BaseModel):

    class Config:
        orm_mode = True


class Lateral2D(ORMBaseModel):
    id: int
    type = constants.Later2dType
    # the_geom
    timeseries: str


class BoundaryConditions2D(ORMBaseModel):
    id: int
    display_name: str
    timeseries: str
    boundary_type: constants.BoundaryType
    # the_geom


class CalculationPoint(ORMBaseModel):
    id: int
    content_type_id: int
    user_ref: constr(max_length=80)
    calc_type: int
    # the_geom


class ControlDelta(ORMBaseModel):
    id: int
    measure_variable: Optional[constr(max_length=50)]
    measure_delta: Optional[constr(max_length=50)]
    measure_dt: Optional[constr(max_length=50)]
    action_type: Optional[constr(max_length=50)]
    action_value: Optional[constr(max_length=50)]
    action_time: Optional[float]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]


class ControlGroup(ORMBaseModel):
    id: int
    name: Optional[constr(max_length=100)]
    description: Optional[str]


class ControlMeasureGroup(ORMBaseModel):
    id: int


class ControlMeasureMap(ORMBaseModel):
    id: int
    measure_group: Optional[ControlMeasureGroup]
    object_type: Optional[constr(max_length=100)]
    object_id: Optional[int]
    weight: Optional[float]


class ControlMemory(ORMBaseModel):
    id: int
    measure_variable: Optional[constr(max_length=50)]
    upper_threshold: Optional[float]
    lower_threshold: Optional[float]
    action_type: Optional[constr(max_length=50)]
    action_value: Optional[constr(max_length=50)]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]
    is_active = bool
    is_inverse = bool


class ControlPID(ORMBaseModel):
    id: int
    measure_variable: Optional[constr(max_length=50)]
    setpoint: Optional[float]
    kp: Optional[float]
    ki: Optional[float]
    kd: Optional[float]
    action_type: Optional[constr(max_length=50)]
    target_type: Optional[constr(max_length=100)]
    target_upper_limit: Optional[constr(max_length=50)]
    target_lower_limit: Optional[constr(max_length=50)]


class ControlTable(ORMBaseModel):
    id: int
    action_table: Optional[str]
    action_type: Optional[constr(max_length=50)]
    measure_variable: Optional[constr(max_length=50)]
    measure_operator: Optional[constr(max_length=2)]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]


class ControlTimed(ORMBaseModel):
    id: int
    action_type: Optional[constr(max_length=50)]
    action_table: Optional[str]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]


class Control(ORMBaseModel):
    id: int
    control_group: Optional[ControlGroup]
    measure_group: Optional[ControlMeasureGroup]
    control_type: Optional[constr(max_length=15)]
    control_id: Optional[int]
    start: Optional[constr(max_length=50)]
    end: Optional[constr(max_length=50)]
    measure_frequency: Optional[int]


class Floodfill(ORMBaseModel):
    id: int
    waterlevel: Optional[float]
    # the_geom


class Interflow(ORMBaseModel):
    id: int
    interflow_type: constants.InterflowType
    porosity: Optional[float]
    porosity_file: Optional[constr(max_length=255)]
    porosity_layer_thickness: Optional[float]
    impervious_layer_elevation: Optional[float]
    hydraulic_conductivity: Optional[float]
    hydraulic_conductivity_file: Optional[constr(max_length=255)]
    display_name: constr(max_length=255)


class PumpedDrainageArea(ORMBaseModel):
    id: int
    name: constr(max_length=64)
    code: constr(max_length=100)
    # the_geom


class SimpleInfiltration(ORMBaseModel):
    id: int
    infiltration_rate: float
    infiltration_rate_file: Optional[constr(max_length=255)]
    infiltration_surface_option = constants.InfiltrationSurfaceOption
    max_infiltration_capacity_file: Optional[str]
    display_name: constr(max_length=255)


class SurfaceParameter(ORMBaseModel):
    id: int
    outflow_delay: float
    surface_layer_thickness: float
    infiltration: bool
    max_infiltration_capacity: float
    min_infiltration_capacity: float
    infiltration_decay_constant: float
    infiltration_recovery_constant: float


class Surface(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    zoom_category = constants.ZoomCategories
    nr_of_inhabitants: Optional[float]
    dry_weather_flow: Optional[float]
    function: Optional[constr(max_length=64)]
    area: Optional[float]
    surface_parameters = SurfaceParameter
    # the_geom


class GroundWater(ORMBaseModel):
    id: int
    groundwater_impervious_layer_level: Optional[float]
    groundwater_impervious_layer_level_file: Optional[constr(max_length=255)]
    groundwater_impervious_layer_level_type: Optional[constants.InitializationType]
    phreatic_storage_capacity: Optional[float]
    phreatic_storage_capacity_file: Optional[constr(max_length=255)]
    phreatic_storage_capacity_type: Optional[constants.InitializationType]
    equilibrium_infiltration_rate: Optional[float]
    equilibrium_infiltration_rate_file: Optional[constr(max_length=255)]
    equilibrium_infiltration_rate_type: Optional[constants.InitializationType]
    initial_infiltration_rate: Optional[float]
    initial_infiltration_rate_file: Optional[constr(max_length=255)]
    initial_infiltration_rate_type: Optional[constants.InitializationType]
    infiltration_decay_period: Optional[float]
    infiltration_decay_period_file: Optional[constr(max_length=255)]
    infiltration_decay_period_type: Optional[constants.InitializationType]
    groundwater_hydro_connectivity: Optional[float]
    groundwater_hydro_connectivity_file: Optional[constr(max_length=255)]
    groundwater_hydro_connectivity_type: Optional[constants.InitializationType]
    display_name: constr(max_length=255)
    leakage: Optional[float]
    leakage_file: Optional[constr(max_length=255)]


class GridRefinement(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    refinement_level: int
    # the_geom
    code: constr(max_length=100)


class GridRefinementArea(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    refinement_level: int
    code: constr(max_length=100)
    # the_geom


class CrossSectionDefinition(ORMBaseModel):
    id: int
    width: Optional[constr(max_length=255)]
    height: Optional[constr(max_length=255)]
    shape: constants.CrossSectionShape
    code: constr(max_length=100)


class ConnectionNode(ORMBaseModel):
    id: int
    storage_area: Optional[float]
    initial_waterlevel: Optional[float]
    # the_geom
    # the_geom_linestring
    code: constr(max_length=100)


class Lateral1d(ORMBaseModel):
    id: int
    connection_node_id: ConnectionNode
    timeseries: str


class Manhole(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    zoom_category: Optional[constants.ZoomCategories]
    shape: Optional[constr(max_length=4)]
    width: Optional[float]
    length: Optional[float]
    surface_level: Optional[float]
    bottom_level: Optional[float]
    drain_level: Optional[float]
    sediment_level: Optional[float]
    manhole_indicator: Optional[int]
    calculation_type: Optional[constants.CalculationTypeNode]
    connection_node: ConnectionNode


class NumericalSettings(ORMBaseModel):
    id: int
    cfl_strictness_factor_1d: Optional[float]
    cfl_strictness_factor_2d: Optional[float]
    convergence_cg: Optional[float]
    convergence_eps: Optional[float]
    flow_direction_threshold: Optional[float]
    frict_shallow_water_correction: Optional[int]
    general_numerical_threshold: Optional[float]
    integration_method: Optional[int]
    limiter_grad_1d: Optional[int]
    limiter_grad_2d: Optional[int]
    limiter_slope_crossectional_area_2d: Optional[int]
    limiter_slope_friction_2d: Optional[int]
    max_nonlin_iterations: Optional[int]
    max_degree: int
    minimum_friction_velocity: Optional[float]
    minimum_surface_area: Optional[float]
    precon_cg: Optional[int]
    preissmann_slot: Optional[float]
    pump_implicit_ratio: Optional[float]
    thin_water_layer_definition: Optional[float]
    use_of_cg: int
    use_of_nested_newton: int


class GlobalSetting(ORMBaseModel):
    id: int
    use_2d_flow: bool
    use_1d_flow: bool
    manhole_storage_area: Optional[float]
    name: Optional[constr(max_length=128)]
    sim_time_step: float
    output_time_step: Optional[float]
    nr_timesteps: int
    start_time: Optional[datetime]
    start_date: date
    grid_space: float
    dist_calc_points: float
    kmax: int
    guess_dams: Optional[int]
    table_step_size: float
    flooding_threshold: float
    advection_1d: int
    advection_2d: int
    dem_file: Optional[constr(max_length=255)]
    frict_type: Optional[int]
    frict_coef: float
    frict_coef_file: Optional[constr(max_length=255)]
    water_level_ini_type: Optional[constants.InitializationType]
    initial_waterlevel: float
    initial_waterlevel_file: Optional[constr(max_length=255)]
    interception_global: Optional[float]
    interception_file: Optional[constr(max_length=255)]
    dem_obstacle_detection: bool
    dem_obstacle_height: Optional[float]
    embedded_cutoff_threshold: Optional[float]
    epsg_code: Optional[int]
    timestep_plus: bool
    max_angle_1d_advection: Optional[float]
    minimum_sim_time_step: Optional[float]
    maximum_sim_time_step: Optional[float]
    frict_avg: Optional[int]
    wind_shielding_file: Optional[constr(max_length=255)]
    use_0d_inflow: int
    table_step_size_1d: Optional[float]
    table_step_size_volume_2d: Optional[float]
    use_2d_rain: int
    initial_groundwater_level: Optional[float]
    initial_groundwater_level_file: Optional[constr(max_length=255)]
    initial_groundwater_level_type: Optional[constants.InitializationType]
    numerical_settings: NumericalSettings
    interflow_settings: Optional[Interflow]
    control_group: Optional[ControlGroup]
    simple_infiltration_settings: Optional[SimpleInfiltration]
    groundwater_settings: Optional[GroundWater]


class AggregationSettings(ORMBaseModel):
    id: int
    global_settings: GlobalSetting
    var_name: constr(max_length=100)
    flow_variable: constants.FlowVariable
    aggregation_method: Optional[constants.AggregationMethod]
    aggregation_in_space: bool
    timestep: int


class BoundaryCondition1D(ORMBaseModel):
    id: int
    boundary_type: constants.BoundaryType
    timeseries: str
    connection_node: ConnectionNode


class SurfaceMap(ORMBaseModel):
    id: int
    surface_type: constants.SurfaceType
    surface_id: int
    connection_node: ConnectionNode
    percentage: Optional[float]


class Channel(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    calculation_type: constants.CalculationType
    dist_calc_points: Optional[float]
    zoom_category: Optional[constants.ZoomCategories]
    # the_geom
    connection_node_start: ConnectionNode
    connection_node_end: ConnectionNode


class Windshielding(ORMBaseModel):
    id: int
    north: Optional[float]
    northeast: Optional[float]
    east: Optional[float]
    southeast: Optional[float]
    south: Optional[float]
    southwest: Optional[float]
    west: Optional[float]
    northwest: Optional[float]
    #the_geom
    channel: Channel


class CrossSectionLocation(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    reference_level: float
    friction_type: constants.FrictionType
    friction_value: float
    bank_level: Optional[float]
    #the_geom
    channel: Channel
    definition: CrossSectionDefinition


class Pipe(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    profile_num: Optional[int]
    sewerage_type: Optional[constants.SewerageType]
    calculation_type: constants.InitializationType
    invert_level_start_point: float
    invert_level_end_point: float
    friction_value: float
    friction_type: constants.FrictionType
    dist_calc_points: Optional[float]
    material: Optional[int]
    original_length: Optional[float]
    zoom_category: Optional[constants.ZoomCategories]
    connection_node_start: ConnectionNode
    connection_node_end: ConnectionNode
    cross_section_definition: CrossSectionDefinition


class Culvert(ORMBaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    calculation_type: Optional[constants.CalculationTypeCulvert]
    friction_value: float
    friction_type: constants.FrictionType
    dist_calc_points: Optional[float]
    zoom_category: Optional[constants.ZoomCategories]
    discharge_coefficient_positive: float
    discharge_coefficient_negative: float
    invert_level_start_point: Optional[float]
    invert_level_end_point: Optional[float]
    #the_geom
    connection_node_start: ConnectionNode
    connection_node_end: ConnectionNode
    cross_section_definition: CrossSectionDefinition


class DemAverageArea(ORMBaseModel):
    id: int
    # the_geom


class Weir(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    display_name: constr(max_length=255)
    crest_level: float
    crest_type: constants.CrestType
    friction_value: float
    friction_type: constants.FrictionType
    discharge_coefficient_positive: float
    discharge_coefficient_negative: float
    sewerage: bool
    external: Optional[float]
    zoom_category: Optional[constants.ZoomCategories]
    connection_node_start: ConnectionNode
    connection_node_end: ConnectionNode
    cross_section_definition: CrossSectionDefinition


class Orifice(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    display_name: constr(max_length=255)
    zoom_category: Optional[constants.ZoomCategories]
    crest_type: constants.CrestType
    crest_level: float
    friction_value: float
    friction_type: constants.FrictionType
    discharge_coefficient_positive: Optional[float]
    discharge_coefficient_negative: Optional[float]
    sewerage: bool
    connection_node_start: ConnectionNode
    connection_node_end: ConnectionNode
    cross_section_definition: CrossSectionDefinition


class Pumpstation(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    display_name: constr(max_length=255)
    zoom_category: Optional[constants.ZoomCategories]
    classification: Optional[int]
    sewerage: bool
    type_: constants.PumpType
    start_level: float
    lower_stop_level: float
    upper_stop_level: Optional[float]
    capacity: float
    connection_node_start: ConnectionNode
    connection_node_end: Optional[ConnectionNode]


class Obstacle(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    crest_level: float
    # the_geom


class Levee(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    crest_level: Optional[float]
    # the_geom
    material: Material
    max_breach_depth:  Optional[float]


class ConnectedPoint(ORMBaseModel):
    id: int
    calculation_pnt: CalculationPoint
    levee: Optional[Levee]
    exchange_level: Optional[float]
    # the_geom


class ImperviousSurface(ORMBaseModel):
    id: int
    code: constr(max_length=100)
    display_name: constr(max_length=255)
    surface_inclination: constants.SurfaceInclinationType
    surface_class: constants.SurfaceClass
    surface_sub_class: Optional[constr(max_length=128)]
    zoom_category: Optional[constants.ZoomCategories]
    nr_of_inhabitants: Optional[float]
    area: Optional[float]
    dry_weather_flow: Optional[float]
    # the_geom


class ImperviousSurfaceMap(ORMBaseModel):
    id: int
    percentage: float
    impervious_surface: ImperviousSurface
    connection_node: ConnectionNode
