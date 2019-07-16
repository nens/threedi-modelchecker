from typing import Optional

from geoalchemy2.types import Geometry
from geoalchemy2.elements import WKBElement
from pydantic import BaseModel, constr, validator

from . import constants, models
from .constants import Material, CalculationType


class Lateral2D(BaseModel):
    id: int
    type = constants.Later2dType
    # the_geom
    timeseries: str

    class Config:
        orm_mode = True


class BoundaryConditions2D(BaseModel):
    id: int
    display_name: str
    timeseries: str
    boundary_type: constants.BoundaryType
    # the_geom

    class Config:
        orm_mode = True


class CalculationPoint(BaseModel):
    id: int
    content_type_id: int
    user_ref: constr(max_length=80)
    calc_type: int
    # the_geom

    class Config:
        orm_mode = True


class ControlDelta(BaseModel):
    id: int
    measure_variable: Optional[constr(max_length=50)]
    measure_delta: Optional[constr(max_length=50)]
    measure_dt: Optional[constr(max_length=50)]
    action_type: Optional[constr(max_length=50)]
    action_value: Optional[constr(max_length=50)]
    action_time: Optional[float]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]

    class Config:
        orm_mode = True

class ControlGroup(BaseModel):
    id: int
    name: Optional[constr(max_length=100)]
    description: Optional[str]

    class Config:
        orm_mode = True


class ControlMeasureGroup(BaseModel):
    id: int


class ControlMeasureMap(BaseModel):
    id: int
    measure_group_id: Optional[ControlMeasureGroup]
    object_type: Optional[constr(max_length=100)]
    object_id: Optional[int]
    weight: Optional[float]


class ControlMemory(BaseModel):
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


class ControlPID(BaseModel):
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


class ControlTable(BaseModel):
    id: int
    action_table: Optional[str]
    action_type: Optional[constr(max_length=50)]
    measure_variable: Optional[constr(max_length=50)]
    measure_operator: Optional[constr(max_length=2)]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]


class ControlTimed(BaseModel):
    id: int
    action_type: Optional[constr(max_length=50)]
    action_table: Optional[str]
    target_type: Optional[constr(max_length=100)]
    target_id: Optional[int]


class Control(BaseModel):
    id: int
    control_group_id: ControlGroup
    measure_group_id: ControlMeasureGroup
    control_type: Optional[constr(max_length=15)]
    control_id: Optional[int]
    start: Optional[constr(max_length=50)]
    end: Optional[constr(max_length=50)]
    measure_frequency: Optional[int]


class Floodfill(BaseModel):
    id: int
    waterlevel: Optional[float]
    # the_geom


class Interflow(BaseModel):
    id: int
    interflow_type: constants.InterflowType
    porosity: Optional[float]
    porosity_file: Optional[constr(max_length=255)]
    porosity_layer_thickness: Optional[float]
    impervious_layer_elevation: Optional[float]
    hydraulic_conductivity: Optional[float]
    hydraulic_conductivity_file: Optional[constr(max_length=255)]
    display_name: Optional[constr(max_length=255)]


class PumpedDrainageArea(BaseModel):
    id: int
    name: constr(max_length=64)
    code: constr(max_length=100)
    # the_geom


class SimpleInfiltration(BaseModel):
    id: int
    infiltration_rate: float
    infiltration_rate_file: Optional[constr(max_length=255)]
    infiltration_surface_option = constants.InfiltrationSurfaceOption
    max_infiltration_capacity_file: Optional[str]
    display_name: constr(max_length=255)


class SurfaceParameter(BaseModel):
    id: int
    outflow_delay: float
    surface_layer_thickness: float
    infiltration: bool
    max_infiltration_capacity: float
    min_infiltration_capacity: float
    infiltration_decay_constant: float
    infiltration_recovery_constant: float


class Surface(BaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    zoom_category = constants.ZoomCategories
    nr_of_inhabitants: Optional[float]
    dry_weather_flow: Optional[float]
    function: Optional[constr(max_length=64)]
    area: Optional[float]
    surface_parameters_id = SurfaceParameter
    # the_geom


class GroundWater(BaseModel):
    id: int
    groundwater_impervious_layer_level: Optional[float]
    groundwater_impervious_layer_level_file: Optional[constr(max_length=255)]
    groundwater_impervious_layer_level_type: constants.InitializationType
    phreatic_storage_capacity: Optional[float]
    phreatic_storage_capacity_file: Optional[constr(max_length=255)]
    phreatic_storage_capacity_type: constants.InitializationType
    equilibrium_infiltration_rate: Optional[float]
    equilibrium_infiltration_rate_file: Optional[constr(max_length=255)]
    equilibrium_infiltration_rate_type: constants.InitializationType
    initial_infiltration_rate: Optional[float]
    initial_infiltration_rate_file: Optional[constr(max_length=255)]
    initial_infiltration_rate_type: constants.InitializationType
    infiltration_decay_period: Optional[float]
    infiltration_decay_period_file: Optional[constr(max_length=255)]
    infiltration_decay_period_type: constants.InitializationType
    groundwater_hydro_connectivity: Optional[float]
    groundwater_hydro_connectivity_file: Optional[constr(max_length=255)]
    groundwater_hydro_connectivity_type: constants.InitializationType
    display_name: constr(max_length=255)
    leakage: Optional[float]
    leakage_file: Optional[constr(max_length=255)]



class GridRefinement(BaseModel):
    id: int
    display_name: constr(max_length=255)
    refinement_level: int
    # the_geom
    code: constr(max_length=100)


class GridRefinementArea(BaseModel):
    id: int
    display_name: constr(max_length=255)
    refinement_level: int
    code: constr(max_length=100)
    # the_geom


class CrossSectionDefinition(BaseModel):
    id: int
    width: Optional[constr(max_length=255)]
    height: Optional[constr(max_length=255)]
    shape: constants.CrossSectionShape
    code: constr(max_length=100)


class ConnectionNode(BaseModel):
    id: int
    storage_area: Optional[float]
    initial_waterlevel: Optional[float]
    # the_geom
    # the_geom_linestring
    code: constr(max_length=100)

    class Config:
        orm_mode = True


class Lateral1d(BaseModel):
    id: int
    connection_node_id: ConnectionNode
    timeseries: str


class Manhole(BaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    zoom_category: constants.ZoomCategories
    shape: Optional[constr(max_length=4)]
    width: Optional[float]
    length: Optional[float]
    surface_level: Optional[float]
    bottom_level: Optional[float]
    drain_level: Optional[float]
    sediment_level: Optional[float]
    manhole_indicator: Optional[int]
    calculation_type: constants.CalculationTypeNode
    connection_node_id: ConnectionNode


class NumericalSettings(BaseModel):
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





class Channel(BaseModel):
    id: int
    display_name: constr(max_length=255)
    code: constr(max_length=100)
    calculation_type: constants.CalculationType
    dist_calc_points: Optional[float]
    zoom_category: Optional[constants.ZoomCategories]
    connection_node_start: ConnectionNode
    connection_node_end: ConnectionNode

    class Config:
        orm_mode = True


class Levee(BaseModel):
    id: int
    code: constr(max_length=100)
    crest_level: Optional[float]
    material: Material
    max_breach_depth:  Optional[float]

    class Config:
        orm_mode = True
