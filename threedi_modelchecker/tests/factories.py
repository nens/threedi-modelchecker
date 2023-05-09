import datetime
from inspect import isclass

import factory
from factory import Faker
from threedi_schema import constants, models


def inject_session(session):
    """Inject the session into all factories"""
    for _, cls in globals().items():
        if isclass(cls) and issubclass(cls, factory.alchemy.SQLAlchemyModelFactory):
            cls._meta.sqlalchemy_session = session


class GlobalSettingsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.GlobalSetting
        sqlalchemy_session = None

    nr_timesteps = 120
    initial_waterlevel = -9999
    numerical_settings_id = 1
    dem_obstacle_detection = False
    frict_avg = 0
    grid_space = 20
    advection_2d = 1
    dist_calc_points = 15
    start_date = datetime.datetime.now()
    table_step_size = 0.05
    use_1d_flow = False
    use_2d_rain = 1
    kmax = 4
    sim_time_step = 30
    minimum_sim_time_step = 1
    output_time_step = 300
    frict_coef = 0.03
    timestep_plus = False
    flooding_threshold = 0.01
    use_2d_flow = True
    advection_1d = 1
    use_0d_inflow = 0
    control_group_id = 1
    frict_type = constants.FrictionType.CHEZY


class SimpleInfiltrationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.SimpleInfiltration
        sqlalchemy_session = None

    infiltration_rate = 0.0


class ControlGroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlGroup
        sqlalchemy_session = None


class ConnectionNodeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ConnectionNode
        sqlalchemy_session = None

    code = Faker("name")
    the_geom = "SRID=4326;POINT(-71.064544 42.28787)"


class ChannelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Channel
        sqlalchemy_session = None

    display_name = Faker("name")
    code = "code"
    calculation_type = constants.CalculationType.CONNECTED
    the_geom = "SRID=4326;LINESTRING(-71.064544 42.28787, -71.0645 42.287)"
    connection_node_start = factory.SubFactory(ConnectionNodeFactory)
    connection_node_end = factory.SubFactory(ConnectionNodeFactory)


class ManholeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Manhole
        sqlalchemy_session = None

    code = Faker("name")
    display_name = Faker("name")
    bottom_level = 0.0
    connection_node = factory.SubFactory(ConnectionNodeFactory)


class WeirFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Weir
        sqlalchemy_session = None

    code = factory.Sequence(lambda n: "Code %d" % n)
    display_name = "display_name"
    crest_level = 1.0
    crest_type = constants.CrestType.BROAD_CRESTED
    friction_value = 2.0
    friction_type = constants.FrictionType.CHEZY
    sewerage = False
    cross_section_definition_id = 1
    connection_node_start_id = 1
    connection_node_end_id = 1


class BoundaryConditions2DFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.BoundaryConditions2D
        sqlalchemy_session = None

    boundary_type = constants.BoundaryType.WATERLEVEL.value
    timeseries = "0,-0.5"
    display_name = Faker("name")


class BoundaryConditions1DFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.BoundaryCondition1D
        sqlalchemy_session = None

    boundary_type = constants.BoundaryType.WATERLEVEL
    timeseries = "0,-0.5"
    connection_node = factory.SubFactory(ConnectionNodeFactory)


class PumpstationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Pumpstation
        sqlalchemy_session = None

    code = "code"
    display_name = "display_name"
    sewerage = False
    type_ = constants.PumpType.DELIVERY_SIDE
    start_level = 1.0
    lower_stop_level = 0.0
    capacity = 5.0
    connection_node_start = factory.SubFactory(ConnectionNodeFactory)


class CrossSectionDefinitionFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.CrossSectionDefinition
        sqlalchemy_session = None

    code = "cross-section code"


class CrossSectionLocationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.CrossSectionLocation
        sqlalchemy_session = None

    code = "code"
    reference_level = 0.0
    friction_type = constants.FrictionType.CHEZY
    friction_value = 0.0
    the_geom = "SRID=4326;POINT(-71.064544 42.28787)"
    channel = factory.SubFactory(ChannelFactory)
    definition = factory.SubFactory(CrossSectionDefinitionFactory)


class AggregationSettingsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.AggregationSettings
        sqlalchemy_session = None

    var_name = Faker("name")
    flow_variable = "waterlevel"
    aggregation_method = "avg"
    timestep = 10


class NumericalSettingsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.NumericalSettings
        sqlalchemy_session = None

    max_degree = 1
    use_of_cg = 20
    use_of_nested_newton = 0


class Lateral1dFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Lateral1d
        sqlalchemy_session = None

    timeseries = "0,-0.1"
    connection_node = factory.SubFactory(ConnectionNodeFactory)


class Lateral2DFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Lateral2D
        sqlalchemy_session = None

    timeseries = "0,-0.2"
    the_geom = "SRID=4326;POINT(-71.064544 42.28787)"
    type = constants.Later2dType.SURFACE


class ImperviousSurfaceFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ImperviousSurface
        sqlalchemy_session = None

    surface_class = "pand"
    surface_inclination = "vlak"
    area = 0.0


class ImperviousSurfaceMapFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ImperviousSurfaceMap
        sqlalchemy_session = None

    percentage = 100.0


class SurfaceParameterFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.SurfaceParameter
        sqlalchemy_session = None

    outflow_delay = 10.0
    surface_layer_thickness = 5.0
    infiltration = True
    max_infiltration_capacity = 10.0
    min_infiltration_capacity = 5.0
    infiltration_decay_constant = 3.0
    infiltration_recovery_constant = 2.0


class SurfaceFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Surface
        sqlalchemy_session = None

    area = 0.0
    surface_parameters = factory.SubFactory(SurfaceParameterFactory)


class SurfaceMapFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.SurfaceMap
        sqlalchemy_session = None

    percentage = 100.0


class ControlTableFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlTable
        sqlalchemy_session = None

    action_type = constants.ControlTableActionTypes.set_discharge_coefficients
    action_table = "0.0;-1.0;2.0#1.0;-1.1;2.1"
    measure_operator = constants.MeasureOperators.greater_than
    measure_variable = constants.MeasureVariables.waterlevel
    target_type = constants.StructureControlTypes.channel
    target_id = 10


class ControlMemoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlMemory
        sqlalchemy_session = None

    action_type = constants.ControlTableActionTypes.set_discharge_coefficients
    action_value = "0.0 -1.0"
    measure_variable = constants.MeasureVariables.waterlevel
    target_type = constants.StructureControlTypes.channel
    target_id = 10
    is_inverse = False
    is_active = True
    upper_threshold = 1.0
    lower_threshold = -1.0


class ControlMeasureGroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlMeasureGroup
        sqlalchemy_session = None


class ControlMeasureMapFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlMeasureMap
        sqlalchemy_session = None

    object_type = "v2_connection_nodes"
    object_id = 101
    weight = 0.1


class ControlFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Control
        sqlalchemy_session = None

    start = "0"
    end = "300"
    measure_frequency = 10


class CulvertFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Culvert
        sqlalchemy_session = None

    code = "code"
    display_name = Faker("name")
    calculation_type = constants.CalculationTypeCulvert.ISOLATED_NODE
    the_geom = "SRID=4326;LINESTRING(-71.064544 42.28787, -71.0645 42.287)"
    connection_node_start = factory.SubFactory(ConnectionNodeFactory)
    connection_node_end = factory.SubFactory(ConnectionNodeFactory)
    friction_value = 0.03
    friction_type = 2
    invert_level_start_point = 0.1
    invert_level_end_point = 1.1
    cross_section_definition = factory.SubFactory(CrossSectionDefinitionFactory)
    discharge_coefficient_negative = 1.0
    discharge_coefficient_positive = 1.0


class PotentialBreachFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.PotentialBreach
        sqlalchemy_session = None

    display_name = Faker("name")
    code = "code"
    the_geom = "SRID=4326;LINESTRING(-71.06452 42.2874, -71.06452 42.286)"
    channel = factory.SubFactory(ChannelFactory)


class VegetationDragFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.VegetationDrag
        sqlalchemy_session = None

    display_name = Faker("name")
    vegetation_height = 1.0
    vegetation_height_file = "vegetation_height_file.txt"

    vegetation_stem_count = 50000
    vegetation_stem_count_file = "vegetation_stem_count_file.txt"

    vegetation_stem_diameter = 0.5
    vegetation_stem_diameter_file = "vegetation_stem_diameter_file.txt"

    vegetation_drag_coefficient = 0.4
    vegetation_drag_coefficient_file = "vegetation_drag_coefficient_file.txt"
