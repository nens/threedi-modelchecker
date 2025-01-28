from inspect import isclass

import factory
from factory import Faker
from threedi_schema import constants, models

# Default geometry strings

DEFAULT_POINT = "SRID=28992;POINT (142742 473443)"
# line from DEFAULT_POINT to another point
DEFAULT_LINE = "SRID=28992;LINESTRING (142742 473443, 142747 473448)"
# polygon containing DEFAULT_POINT
DEFAULT_POLYGON = "SRID=28992;POLYGON ((142742 473443, 142743 473443, 142744 473444, 142742 473444, 142742 473443))"


def inject_session(session):
    """Inject the session into all factories"""
    for _, cls in globals().items():
        if isclass(cls) and issubclass(cls, factory.alchemy.SQLAlchemyModelFactory):
            cls._meta.sqlalchemy_session = session


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True

    id = factory.Sequence(lambda n: n + 1)


class TimeStepSettingsFactory(BaseFactory):
    class Meta:
        model = models.TimeStepSettings
        sqlalchemy_session = None

    time_step = 30
    min_time_step = 1
    max_time_step = 100
    output_time_step = 300
    use_time_step_stretch = False


class ModelSettingsFactory(BaseFactory):
    class Meta:
        model = models.ModelSettings
        sqlalchemy_session = None

    friction_averaging = 0
    minimum_cell_size = 20
    calculation_point_distance_1d = 15
    minimum_table_step_size = 0.05
    use_1d_flow = False
    use_2d_rain = 1
    nr_grid_levels = 4
    friction_coefficient = 0.03
    use_2d_flow = True
    friction_type = constants.FrictionType.CHEZY


class ConnectionNodeFactory(BaseFactory):
    class Meta:
        model = models.ConnectionNode
        sqlalchemy_session = None

    code = Faker("name")
    geom = DEFAULT_POINT


class ChannelFactory(BaseFactory):
    class Meta:
        model = models.Channel
        sqlalchemy_session = None

    display_name = Faker("name")
    code = Faker("name")
    exchange_type = constants.CalculationType.CONNECTED
    geom = DEFAULT_LINE


class WeirFactory(BaseFactory):
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
    connection_node_id_start = 1
    connection_node_id_end = 1
    geom = DEFAULT_LINE


class BoundaryConditions2DFactory(BaseFactory):
    class Meta:
        model = models.BoundaryConditions2D
        sqlalchemy_session = None

    type = constants.BoundaryType.WATERLEVEL.value
    timeseries = "0,-0.5"
    display_name = Faker("name")
    geom = DEFAULT_LINE


class BoundaryConditions1DFactory(BaseFactory):
    class Meta:
        model = models.BoundaryCondition1D
        sqlalchemy_session = None

    type = constants.BoundaryType.WATERLEVEL
    timeseries = "0,-0.5"
    connection_node_id = 1
    geom = DEFAULT_POINT


class PumpMapFactory(BaseFactory):
    class Meta:
        model = models.PumpMap
        sqlalchemy_session = None

    geom = DEFAULT_POINT


class PumpFactory(BaseFactory):
    class Meta:
        model = models.Pump
        sqlalchemy_session = None

    code = "code"
    display_name = "display_name"
    sewerage = False
    type_ = constants.PumpType.DELIVERY_SIDE
    start_level = 1.0
    lower_stop_level = 0.0
    capacity = 5.0
    geom = DEFAULT_POINT


class CrossSectionLocationFactory(BaseFactory):
    class Meta:
        model = models.CrossSectionLocation
        sqlalchemy_session = None

    code = "code"
    reference_level = 0.0
    friction_type = constants.FrictionType.CHEZY
    friction_value = 0.0
    geom = DEFAULT_POINT


class AggregationSettingsFactory(BaseFactory):
    class Meta:
        model = models.AggregationSettings
        sqlalchemy_session = None

    flow_variable = "waterlevel"
    aggregation_method = "avg"
    interval = 10


class NumericalSettingsFactory(BaseFactory):
    class Meta:
        model = models.NumericalSettings
        sqlalchemy_session = None

    max_degree_gauss_seidel = 1
    use_of_cg = 20
    use_nested_newton = 0
    flooding_threshold = 0.01


class Lateral1DFactory(BaseFactory):
    class Meta:
        model = models.Lateral1D
        sqlalchemy_session = None

    timeseries = "0,-0.1"
    connection_node_id = 1
    geom = DEFAULT_POINT


class Lateral2DFactory(BaseFactory):
    class Meta:
        model = models.Lateral2D
        sqlalchemy_session = None

    timeseries = "0,-0.2"
    geom = DEFAULT_POINT
    type = constants.Later2dType.SURFACE


class SurfaceParametersFactory(BaseFactory):
    class Meta:
        model = models.SurfaceParameters
        sqlalchemy_session = None

    outflow_delay = 10.0
    surface_layer_thickness = 5.0
    infiltration = True
    max_infiltration_capacity = 10.0
    min_infiltration_capacity = 5.0
    infiltration_decay_constant = 3.0
    infiltration_recovery_constant = 2.0


class DryWheatherFlowMapFactory(BaseFactory):
    class Meta:
        model = models.DryWeatherFlowMap
        sqlalchemy_session = None

    geom = DEFAULT_POINT


class DryWeatherFlowFactory(BaseFactory):
    class Meta:
        model = models.DryWeatherFlow
        sqlalchemy_session = None

    geom = DEFAULT_POLYGON


class DryWeatherFlowDistributionFactory(BaseFactory):
    class Meta:
        model = models.DryWeatherFlowDistribution
        sqlalchemy_session = None

    id = 1
    distribution = (
        "3,1.5,1,1,0.5,0.5,2.5,8,7.5,6,5.5,5,4.5,4,4,3.5,3.5,4,5.5,8,7,5.5,4.5,4"
    )


class SurfaceFactory(BaseFactory):
    class Meta:
        model = models.Surface
        sqlalchemy_session = None

    area = 0.0
    geom = DEFAULT_POLYGON

    # surface_parameters = factory.SubFactory(SurfaceParameterFactory)


class SurfaceMapFactory(BaseFactory):
    class Meta:
        model = models.SurfaceMap
        sqlalchemy_session = None

    percentage = 100.0
    geom = DEFAULT_LINE


class TagsFactory(BaseFactory):
    class Meta:
        model = models.Tags
        sqlalchemy_session = None


class TableControlFactory(BaseFactory):
    class Meta:
        model = models.TableControl
        sqlalchemy_session = None

    action_type = constants.TableControlActionTypes.set_discharge_coefficients
    action_table = "0.0,-1.0 2.0\n1.0,-1.1 2.1"
    measure_operator = constants.MeasureOperators.greater_than
    target_type = constants.StructureControlTypes.channel
    target_id = 10
    geom = DEFAULT_POINT


class MemoryControlFactory(BaseFactory):
    class Meta:
        model = models.MemoryControl
        sqlalchemy_session = None

    action_type = constants.TableControlActionTypes.set_discharge_coefficients
    action_value_1 = 0.0
    action_value_2 = -1.0
    target_type = constants.StructureControlTypes.channel
    target_id = 10
    is_inverse = False
    is_active = True
    upper_threshold = 1.0
    lower_threshold = -1.0
    geom = DEFAULT_POINT


class MeasureMapFactory(BaseFactory):
    class Meta:
        model = models.MeasureMap
        sqlalchemy_session = None

    control_type = constants.MeasureVariables.waterlevel
    geom = DEFAULT_LINE


class MeasureLocationFactory(BaseFactory):
    class Meta:
        model = models.MeasureLocation
        sqlalchemy_session = None

    geom = DEFAULT_POINT


class CulvertFactory(BaseFactory):
    class Meta:
        model = models.Culvert
        sqlalchemy_session = None

    code = "code"
    display_name = Faker("name")
    exchange_type = constants.CalculationTypeCulvert.ISOLATED_NODE
    geom = DEFAULT_LINE
    friction_value = 0.03
    friction_type = 2
    invert_level_start = 0.1
    invert_level_end = 1.1
    discharge_coefficient_negative = 1.0
    discharge_coefficient_positive = 1.0


class PotentialBreachFactory(BaseFactory):
    class Meta:
        model = models.PotentialBreach
        sqlalchemy_session = None

    display_name = Faker("name")
    code = "code"
    geom = DEFAULT_LINE


class VegetationDragFactory(BaseFactory):
    class Meta:
        model = models.VegetationDrag2D
        sqlalchemy_session = None

    vegetation_height = 1.0
    vegetation_height_file = "vegetation_height_file.txt"

    vegetation_stem_count = 50000
    vegetation_stem_count_file = "vegetation_stem_count_file.txt"

    vegetation_stem_diameter = 0.5
    vegetation_stem_diameter_file = "vegetation_stem_diameter_file.txt"

    vegetation_drag_coefficient = 0.4
    vegetation_drag_coefficient_file = "vegetation_drag_coefficient_file.txt"


class SimulationTemplateSettingsFactory(BaseFactory):
    class Meta:
        model = models.SimulationTemplateSettings
        sqlalchemy_session = None

    name = "Foo"
    use_0d_inflow = constants.InflowType.NO_INFLOW
