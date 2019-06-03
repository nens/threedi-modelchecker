import datetime

import factory
from factory import Faker

from threedi_modelchecker.threedi_model import models, constants
from tests import Session


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
    flow_variable = "max_timestep"
    aggregation_method = "avg"
    aggregation_in_space = False
    timestep = 10


class MigrationHistoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.SouthMigrationHistory
        sqlalchemy_session = Session

    app_name = "my_app"
    migration = "migration %s" % factory.Sequence(lambda n: n)
    applied = datetime.datetime.now()
