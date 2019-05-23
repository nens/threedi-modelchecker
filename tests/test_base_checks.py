import factory
import pytest
from sqlalchemy import func
from sqlalchemy.orm import Query

from tests import factories
from threedi_modelchecker.checks.base import EnumCheck, ConditionalCheck, \
    GeneralCheck
from threedi_modelchecker.checks.base import ForeignKeyCheck
from threedi_modelchecker.checks.base import GeometryCheck
from threedi_modelchecker.checks.base import GeometryTypeCheck
from threedi_modelchecker.checks.base import NotNullCheck
from threedi_modelchecker.checks.base import RangeCheck
from threedi_modelchecker.checks.base import TypeCheck
from threedi_modelchecker.checks.base import UniqueCheck
from threedi_modelchecker.checks.base import sqlalchemy_to_sqlite_type
from threedi_modelchecker.threedi_model import constants, custom_types, models


def test_fk_check(session):
    factories.ManholeFactory.create_batch(5)
    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id,
        models.Manhole.connection_node_id,
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_no_entries(session):
    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id,
        models.Manhole.connection_node_id,
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_null_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    factories.ManholeFactory(manhole_indicator=None)

    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id,
        models.Manhole.manhole_indicator,
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_both_null(session):
    global_settings = factories.GlobalSettingsFactory(control_group_id=None)

    assert session.query(models.GlobalSetting).first().id is not None
    assert session.query(models.GlobalSetting.control_group_id).scalar() is None
    assert session.query(models.ControlGroup.id).scalar() is None
    fk_check = ForeignKeyCheck(
        models.ControlGroup.id,
        models.GlobalSetting.control_group_id,
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_missing_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    missing_fk = factories.ManholeFactory(manhole_indicator=-1)

    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id,
        models.Manhole.manhole_indicator,
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == missing_fk.id


def test_unique_check(session):
    factories.ManholeFactory.create_batch(5)

    unique_check = UniqueCheck(models.Manhole.code)
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_unique_check_duplicate_value(session):
    manholes = factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n))
    duplicate_manhole = factories.ManholeFactory(
        zoom_category=manholes[0].zoom_category)

    unique_check = UniqueCheck(models.Manhole.zoom_category)
    invalid_rows = unique_check.get_invalid(session)

    assert len(invalid_rows) == 2
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert manholes[0].id in invalid_ids
    assert duplicate_manhole.id in invalid_ids


def test_unique_check_null_values(session):
    factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n))
    factories.ManholeFactory.create_batch(3, zoom_category=None)

    unique_check = UniqueCheck(models.ConnectionNode.id)
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_null_check(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)

    null_check = NotNullCheck(models.ConnectionNode.storage_area)
    invalid_rows = null_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_null_check_with_null_value(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)
    null_node = factories.ConnectionNodeFactory(storage_area=None)

    null_check = NotNullCheck(models.ConnectionNode.storage_area)
    invalid_rows = null_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == null_node.id


def test_threedi_db_and_factories(threedi_db):
    """Test to ensure that the threedi_db and factories use the same
    session object."""
    session = threedi_db.get_session()
    manhole = factories.ManholeFactory()
    q = session.query(models.Manhole)
    assert q.count() == 1


def test_run_spatial_function(session):
    """Example how to use spatial functions.

     Works on postgis and spatialite"""
    c1 = factories.ConnectionNodeFactory()
    from geoalchemy2 import func
    q = session.query(func.ST_AsGeoJSON(models.ConnectionNode.the_geom))
    r = q.first()


def test_type_check(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=456)

    type_check = TypeCheck(models.Manhole.zoom_category)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_type_check_integer(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=None)
    m1 = factories.ManholeFactory(zoom_category='abc')
    m2 = factories.ManholeFactory(zoom_category=1.23)

    type_check = TypeCheck(models.Manhole.zoom_category)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 2
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert m1.id in invalid_ids
    assert m2.id in invalid_ids


def test_type_check_varchar(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.ManholeFactory(code='abc')
    factories.ManholeFactory(code=123)

    type_check = TypeCheck(models.Manhole.code)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_type_check_boolean(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.GlobalSettingsFactory(use_1d_flow=True)
    factories.GlobalSettingsFactory(use_1d_flow=1)
    # factories.GlobalSettingsFactory(use_1d_flow='true')
    # factories.GlobalSettingsFactory(use_1d_flow='1')
    # factories.GlobalSettingsFactory(use_1d_flow=1.0)

    type_check = TypeCheck(models.GlobalSetting.use_1d_flow)
    invalid_rows = type_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_check(session):
    c = factories.ConnectionNodeFactory(
        the_geom='SRID=28992;POINT(-371.064544 42.28787)'
    )

    geometry_check = GeometryCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_check.get_invalid(session)

    assert len(invalid_rows ) == 0


def test_geometry_check_with_invalid_geoms(session):
    if session.bind.name == 'postgresql':
        pytest.skip('Not sure how to insert invalid types in postgresql')

    inser_invalid_geom_q = """
    INSERT INTO v2_connection_nodes (id, code, the_geom) 
    VALUES (2, 'the_code', 'invalid_geom')
    """
    session.execute(inser_invalid_geom_q)
    factories.ConnectionNodeFactory(
        the_geom='SRID=28992;POINT(-71.064544 42.28787)'
    )

    geometry_check = GeometryCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_geometry_check_with_none_geoms(session):
    if session.bind.name == 'postgresql':
        pytest.skip('Not sure how to insert invalid types in postgresql')
    factories.ConnectionNodeFactory(
        the_geom_linestring='SRID=4326;LINESTRING(71.0 42.2, 71.3 42.3)'
    )
    none_geom = factories.ConnectionNodeFactory(
            the_geom_linestring=None
    )

    geometry_check = GeometryCheck(models.ConnectionNode.the_geom_linestring)
    invalid_rows = geometry_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_type_check(session):
    factories.ConnectionNodeFactory.create_batch(
        2, the_geom='SRID=28992;POINT(-71.064544 42.28787)'
    )

    geometry_type_check = GeometryTypeCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_type_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_type_check_invalid_geom_type(session):
    if session.bind.name == 'postgresql':
        pytest.skip('Not sure how to insert invalid geometry types in postgresql')
    factories.ConnectionNodeFactory(
        the_geom='SRID=28992;POINT(-71.064544 42.28787)'
    )
    invalid_geom_type = factories.ConnectionNodeFactory(
        the_geom='SRID=28992;LINESTRING(71.0 42.2, 71.3 42.3)'
    )

    geometry_type_check = GeometryTypeCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_type_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == invalid_geom_type.id


def test_enum_check(session):
    factories.BoundaryConditions2DFactory()

    enum_check = EnumCheck(models.BoundaryConditions2D.boundary_type)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows ) == 0


def test_enum_check_with_null_values(session):
    factories.BoundaryConditions2DFactory(boundary_type=None)

    enum_check = EnumCheck(models.BoundaryConditions2D.boundary_type)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_enum_check_with_invalid_value(session):
    factories.BoundaryConditions2DFactory()
    faulty_boundary = factories.BoundaryConditions2DFactory(boundary_type=-1)

    enum_check = EnumCheck(models.BoundaryConditions2D.boundary_type)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == faulty_boundary.id


def test_enum_check_string_enum(session):
    factories.AggregationSettingsFactory()

    enum_check = EnumCheck(models.AggregationSettings.aggregation_method)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_enum_check_string_with_invalid_value(session):
    if session.bind.name == 'postgresql':
        pytest.skip('Not able to add invalid aggregation method due to '
                    'CHECKED CONSTRAINT')
    a = factories.AggregationSettingsFactory(aggregation_method='invalid')

    enum_check = EnumCheck(models.AggregationSettings.aggregation_method)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == a.id


def test_sqlalchemy_to_sqlite_type_with_custom_type():
    customIntegerEnum = custom_types.IntegerEnum(constants.BoundaryType)
    assert sqlalchemy_to_sqlite_type(customIntegerEnum) == 'integer'


def test_range_check(session):
    weir = factories.WeirFactory(discharge_coefficient_negative=5)

    range_check = RangeCheck(column=models.Weir.discharge_coefficient_negative,
                             upper_limit=10, lower_limit=0)
    invalid = range_check.get_invalid(session)
    assert len(invalid) == 0


def test_range_check_out_of_range(session):
    weir = factories.WeirFactory(discharge_coefficient_negative=11)

    range_check = RangeCheck(column=models.Weir.discharge_coefficient_negative,
                             upper_limit=10, lower_limit=0)
    invalid = range_check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == weir.id


def test_conditional_check_get_applicable(session):
    conditional_check = ConditionalCheck(
        criterion=True,
        check=RangeCheck(
            column=models.GlobalSetting.id,
            upper_limit=10
        )
    )
    query = conditional_check.to_check(session)


def test_conditional_checks(session):
    global_settings1 = factories.GlobalSettingsFactory(
        dem_obstacle_detection=True,
        dem_obstacle_height=-5
    )
    global_settings2 = factories.GlobalSettingsFactory(
        dem_obstacle_detection=False,
        dem_obstacle_height=-5
    )

    range_check = RangeCheck(
        column=models.GlobalSetting.dem_obstacle_height,
        lower_limit=0
    )
    conditional_range_check = ConditionalCheck(
        check=range_check,
        criterion=(models.GlobalSetting.dem_obstacle_detection == True)
    )

    invalid_conditional = conditional_range_check.get_invalid(session)
    assert len(invalid_conditional) == 1
    assert invalid_conditional[0].id == global_settings1.id
    invalid_no_condition = range_check.get_invalid(session)
    assert len(invalid_no_condition) == 2


def test_conditional_check_storage_area(session):
    # if connection node is a manhole, then the storage area of the
    # connection_node must be > 0
    conn_node1_valid = factories.ConnectionNodeFactory(storage_area=5)
    conn_node2_valid = factories.ConnectionNodeFactory(storage_area=-3)
    conn_node_manhole_valid = factories.ConnectionNodeFactory(storage_area=4)
    conn_node_manhole_invalid = factories.ConnectionNodeFactory(storage_area=-5)
    manhole_valid = factories.ManholeFactory(connection_node=conn_node_manhole_valid)
    manhole_invalid = factories.ManholeFactory(connection_node=conn_node_manhole_invalid)

    check = ConditionalCheck(
        criterion=(models.ConnectionNode.id == models.Manhole.connection_node_id),
        check=GeneralCheck(
            column=models.ConnectionNode.storage_area,
            criterion_valid=models.ConnectionNode.storage_area > 0
        )
    )
    to_check = check.to_check(session)
    assert to_check.count() == 2

    invalids = check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == conn_node_manhole_invalid.id

    valids = check.get_valid(session)
    assert len(valids) == 1
    assert valids[0].id == conn_node_manhole_valid.id


def test_conditional_check_advanced(session):
    connection_node1 = factories.ConnectionNodeFactory(storage_area=-1)
    connection_node2 = factories.ConnectionNodeFactory(storage_area=-2)
    connection_node3 = factories.ConnectionNodeFactory(storage_area=3)
    connection_node4 = factories.ConnectionNodeFactory(storage_area=4)
    connection_node5 = factories.ConnectionNodeFactory(storage_area=10)
    manhole = factories.ManholeFactory(
        connection_node=connection_node2
    )
    manhole_good = factories.ManholeFactory(
            connection_node=connection_node5
        )

    # If a connection_node is a manhole, then storage_area > 0
    advanced_check = ConditionalCheck(
        criterion=(models.ConnectionNode.id == models.Manhole.connection_node_id),
        check=RangeCheck(
            column=models.ConnectionNode.storage_area,
            lower_limit=0
        )
    )
    invalids = advanced_check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == connection_node2.id
    assert invalids[0].storage_area == connection_node2.storage_area


def test_get_valid(session):
    connection_node1 = factories.ConnectionNodeFactory(storage_area=1)
    connection_node2 = factories.ConnectionNodeFactory(storage_area=2)
    connection_node3 = factories.ConnectionNodeFactory(storage_area=3)

    range_check = RangeCheck(
        column=models.ConnectionNode.storage_area,
        lower_limit=2
    )
    to_check = range_check.to_check(session).all()
    assert len(to_check) == 3
    invalids = range_check.get_invalid(session)
    valids = range_check.get_valid(session)
    assert len(valids) + len(invalids) == 3


def test_general_check_range(session):
    w1 = factories.WeirFactory(friction_value=2)
    w2 = factories.WeirFactory(friction_value=-1)

    invalid_criterion = models.Weir.friction_value > 0
    general_range_check = GeneralCheck(
        column=models.Weir.friction_value,
        criterion_invalid=invalid_criterion
    )

    invalid = general_range_check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == w1.id


def test_general_check_valid_criterion_range(session):
    w1 = factories.WeirFactory(friction_value=2)
    w2 = factories.WeirFactory(friction_value=-1)

    valid_criterion = models.Weir.friction_value >= 0
    general_range_check = GeneralCheck(
        column=models.Weir.friction_value,
        criterion_valid=valid_criterion
    )

    invalid = general_range_check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == w2.id


@pytest.mark.skip('Aggregate function not working for general checks')
def test_general_check_aggregation_function(session):
    # Aggregation functions need something different!

    w1 = factories.WeirFactory(friction_value=2)
    w2 = factories.WeirFactory(friction_value=-1)

    invalid_criterion = func.count(models.Weir.friction_value) < 3
    general_range_check = GeneralCheck(
        column=models.Weir.friction_value,
        criterion_invalid=invalid_criterion
    )

    invalid = general_range_check.get_invalid(session)
    assert len(invalid) == 2
    invalid_ids = [row.id for row in invalid]
    assert w1.id in invalid_ids
    assert w2.id in invalid_ids
