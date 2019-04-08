import datetime

import factory
from factory import Faker
from geoalchemy2 import Geometry

from model_checker import models
from tests import Session


# def fake_ewkt(srid='28992', geom_type='LINESTRING', coords=2):
#     from factory.faker import faker
#     f = faker.Faker()
#     coord_list = ''
#     for _ in range(coords):
#         lat, lng = f.local_latlng(country_code='NL', coords_only=True)
#         coord_list.append('{} {}'.format(lat, lng))
#     r = f'SRID={srid};{geom_type}({coord_list})'


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

    code = Faker('name')
    the_geom = 'SRID=28992;POINT(-71.064544 42.28787)'


class ManholeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Manhole
        sqlalchemy_session = Session

    code = Faker('name')
    display_name = Faker('name')
    connection_node = factory.SubFactory(ConnectionNodeFactory)


class LeveeFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.Levee
        sqlalchemy_session = Session

    code = factory.Sequence(lambda n: "Code %d" % n)
    crest_level = 4
    max_breach_depth = 4
    material = 1
    the_geom = "SRID=28992;LINESTRING(-71.160281 42.258729,-71.160837 42.259113,-71.161144 42.25932)"


class MigrationHistoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = models.SouthMigrationHistory
        sqlalchemy_session = Session

    app_name = 'my_app'
    migration = 'migration %s' % factory.Sequence(lambda n: n)
    applied = datetime.datetime.now()
