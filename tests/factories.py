from factory import Faker
from tests import Session
from threedi_modelchecker.threedi_model import constants
from threedi_modelchecker.threedi_model import models

import datetime
import factory


class GlobalSettingsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.GlobalSetting
        sqlalchemy_session = Session

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
    frict_coef = 0.03
    timestep_plus = False
    flooding_threshold = 0.01
    use_2d_flow = True
    advection_1d = 1
    use_0d_inflow = 0
    control_group_id = 1


class SimpleInfiltrationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.SimpleInfiltration
        sqlalchemy_session = Session

    infiltration_rate = 0.0


class ControlGroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlGroup
        sqlalchemy_session = Session


class ConnectionNodeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ConnectionNode
        sqlalchemy_session = Session

    code = Faker("name")
    the_geom = "SRID=28992;POINT(-71.064544 42.28787)"


class ChannelFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Channel
        sqlalchemy_session = Session

    display_name = Faker("name")
    code = "code"
    calculation_type = constants.CalculationType.CONNECTED
    the_geom = "SRID=4326;LINESTRING(-71.064544 42.28787, -71.0645 42.287)"
    connection_node_start = factory.SubFactory(ConnectionNodeFactory)
    connection_node_end = factory.SubFactory(ConnectionNodeFactory)


class ManholeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Manhole
        sqlalchemy_session = Session

    code = Faker("name")
    display_name = Faker("name")
    connection_node = factory.SubFactory(ConnectionNodeFactory)


class LeveeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Levee
        sqlalchemy_session = Session

    code = factory.Sequence(lambda n: "Code %d" % n)
    crest_level = 4
    max_breach_depth = 4
    material = 1
    the_geom = "SRID=28992;LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"  # noqa


class WeirFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Weir
        sqlalchemy_session = Session

    code = factory.Sequence(lambda n: "Code %d" % n)
    display_name = "display_name"
    crest_level = 1.0
    crest_type = constants.CrestType.BROAD_CRESTED
    friction_value = 2.0
    friction_type = constants.FrictionType.CHEZY
    sewerage = False


class BoundaryConditions2DFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.BoundaryConditions2D
        sqlalchemy_session = Session

    boundary_type = constants.BoundaryType.WATERLEVEL
    timeseries = "0,-0.5"
    display_name = Faker("name")


class BoundaryConditions1DFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.BoundaryCondition1D
        sqlalchemy_session = Session

    boundary_type = constants.BoundaryType.WATERLEVEL
    timeseries = "0,-0.5"
    connection_node = factory.SubFactory(ConnectionNodeFactory)


class PumpstationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Pumpstation
        sqlalchemy_session = Session

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
        sqlalchemy_session = Session

    code = "cross-section code"


class CrossSectionLocationFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.CrossSectionLocation
        sqlalchemy_session = Session

    code = "code"
    reference_level = 0.0
    friction_type = constants.FrictionType.CHEZY
    friction_value = 0.0
    channel = factory.SubFactory(ChannelFactory)
    definition = factory.SubFactory(CrossSectionDefinitionFactory)


class AggregationSettingsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.AggregationSettings
        sqlalchemy_session = Session

    var_name = Faker("name")
    flow_variable = "waterlevel"
    aggregation_method = "avg"
    timestep = 10


class NumericalSettingsFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.NumericalSettings
        sqlalchemy_session = Session

    max_degree = 1
    use_of_cg = 0
    use_of_nested_newton = 0

    
class Lateral1dFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Lateral1d
        sqlalchemy_session = Session

    timeseries = "0.0,-0.1"
    connection_node = factory.SubFactory(ConnectionNodeFactory)  


class Lateral2DFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Lateral2D
        sqlalchemy_session = Session

    timeseries = "0.0,-0.2"
    the_geom = "SRID=28992;POINT(-71.064544 42.28787)"

class ControlTableFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlTable
        sqlalchemy_session = Session

    action_type = "set_discharge_coefficients"
    action_table = "0.0;-1.0"
    measure_operator = ">"
    measure_variable = "waterlevel"
    target_type = "v2_channel"
    target_id = 10


class ControlMemoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlMemory
        sqlalchemy_session = Session

    action_type = "set_discharge_coefficients"
    action_value = "0.0 -1.0"
    measure_variable = "waterlevel"
    target_type = "v2_channel"
    target_id = 10
    is_inverse = False
    is_active = True
    upper_threshold = 1.0
    lower_threshold = -1.0


class ControlTimedFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlTimed
        sqlalchemy_session = Session

    action_type = "set_discharge_coefficients"
    action_table = "0.0 -1.0"
    target_type = "v2_channel"
    target_id = 10


class ControlMeasureGroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlMeasureGroup
        sqlalchemy_session = Session
    

class ControlMeasureMapFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.ControlMeasureMap
        sqlalchemy_session = Session

    object_type = "v2_connection_nodes"
    object_id = 101
    weight = 0.1


class ControlFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Control
        sqlalchemy_session = Session

    start = "0"
    end = "300"
    measure_frequency = 10

    
class CulvertFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Culvert
        sqlalchemy_session = Session

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
