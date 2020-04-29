import factory
import pytest
from sqlalchemy import cast, and_
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy.orm import Query

from tests import factories
from threedi_modelchecker.checks.base import EnumCheck
from threedi_modelchecker.checks.base import GeneralCheck
from threedi_modelchecker.checks.base import ForeignKeyCheck
from threedi_modelchecker.checks.base import GeometryCheck
from threedi_modelchecker.checks.base import GeometryTypeCheck
from threedi_modelchecker.checks.base import QueryCheck
from threedi_modelchecker.checks.base import NotNullCheck
from threedi_modelchecker.checks.base import TypeCheck
from threedi_modelchecker.checks.base import UniqueCheck
from threedi_modelchecker.checks.base import _sqlalchemy_to_sqlite_type
from threedi_modelchecker.threedi_model import constants, custom_types, models


def test_fk_check(session):
    factories.ManholeFactory.create_batch(5)
    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id, models.Manhole.connection_node_id
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_no_entries(session):
    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id, models.Manhole.connection_node_id
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_null_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    factories.ManholeFactory(manhole_indicator=None)

    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id, models.Manhole.manhole_indicator
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_both_null(session):
    factories.GlobalSettingsFactory(control_group_id=None)

    assert session.query(models.GlobalSetting).first().id is not None
    assert session.query(models.GlobalSetting.control_group_id).scalar() is None
    assert session.query(models.ControlGroup.id).scalar() is None
    fk_check = ForeignKeyCheck(
        models.ControlGroup.id, models.GlobalSetting.control_group_id
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_missing_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    missing_fk = factories.ManholeFactory(manhole_indicator=-1)

    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id, models.Manhole.manhole_indicator
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
        5, zoom_category=factory.Sequence(lambda n: n)
    )
    duplicate_manhole = factories.ManholeFactory(
        zoom_category=manholes[0].zoom_category
    )

    unique_check = UniqueCheck(models.Manhole.zoom_category)
    invalid_rows = unique_check.get_invalid(session)

    assert len(invalid_rows) == 2
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert manholes[0].id in invalid_ids
    assert duplicate_manhole.id in invalid_ids


def test_unique_check_null_values(session):
    factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n)
    )
    factories.ManholeFactory.create_batch(3, zoom_category=None)

    unique_check = UniqueCheck(models.ConnectionNode.id)
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_null_check(session):
    factories.ConnectionNodeFactory.create_batch(5, storage_area=3.0)

    null_check = NotNullCheck(models.ConnectionNode.storage_area)
    invalid_rows = null_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_null_check_with_null_value(session):
    factories.ConnectionNodeFactory.create_batch(5, storage_area=3.0)
    null_node = factories.ConnectionNodeFactory(storage_area=None)

    null_check = NotNullCheck(models.ConnectionNode.storage_area)
    invalid_rows = null_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == null_node.id


def test_threedi_db_and_factories(threedi_db):
    """Test to ensure that the threedi_db and factories use the same
    session object."""
    session = threedi_db.get_session()
    factories.ManholeFactory()
    q = session.query(models.Manhole)
    assert q.count() == 1


def test_run_spatial_function(session):
    """Example how to use spatial functions.

     Works on postgis and spatialite"""
    factories.ConnectionNodeFactory()
    from geoalchemy2 import func

    q = session.query(func.ST_AsGeoJSON(models.ConnectionNode.the_geom))
    q.first()


def test_type_check(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=456)

    type_check = TypeCheck(models.Manhole.zoom_category)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_type_check_integer(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=None)
    m1 = factories.ManholeFactory(zoom_category="abc")
    m2 = factories.ManholeFactory(zoom_category=1.23)

    type_check = TypeCheck(models.Manhole.zoom_category)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 2
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert m1.id in invalid_ids
    assert m2.id in invalid_ids


def test_type_check_float_can_store_integer(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ManholeFactory(surface_level=1.3)
    factories.ManholeFactory(surface_level=None)
    factories.ManholeFactory(surface_level=1)
    m1 = factories.ManholeFactory(zoom_category="abc")

    type_check = TypeCheck(models.Manhole.zoom_category)
    invalid_rows = type_check.get_invalid(session)
    valid_rows = type_check.get_valid(session)

    assert len(valid_rows) == 3
    assert len(invalid_rows) == 1
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert m1.id in invalid_ids


def test_type_check_varchar(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ManholeFactory(code="abc")
    factories.ManholeFactory(code=123)

    type_check = TypeCheck(models.Manhole.code)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_type_check_boolean(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.GlobalSettingsFactory(use_1d_flow=True)
    factories.GlobalSettingsFactory(use_1d_flow=1)
    # factories.GlobalSettingsFactory(use_1d_flow='true')
    # factories.GlobalSettingsFactory(use_1d_flow='1')
    # factories.GlobalSettingsFactory(use_1d_flow=1.0)

    type_check = TypeCheck(models.GlobalSetting.use_1d_flow)
    invalid_rows = type_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_check(session):
    factories.ConnectionNodeFactory(
        the_geom="SRID=28992;POINT(-371.064544 42.28787)"
    )

    geometry_check = GeometryCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_geometry_check_with_invalid_geoms(session):
    if session.bind.name == "postgresql":
        pytest.skip("Not sure how to insert invalid types in postgresql")

    inser_invalid_geom_q = """
    INSERT INTO v2_connection_nodes (id, code, the_geom)
    VALUES (2, 'the_code', 'invalid_geom')
    """
    session.execute(inser_invalid_geom_q)
    factories.ConnectionNodeFactory(the_geom="SRID=28992;POINT(-71.064544 42.28787)")

    geometry_check = GeometryCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_geometry_check_with_none_geoms(session):
    if session.bind.name == "postgresql":
        pytest.skip("Not sure how to insert invalid types in postgresql")
    factories.ConnectionNodeFactory(
        the_geom_linestring="SRID=4326;LINESTRING(71.0 42.2, 71.3 42.3)"
    )
    factories.ConnectionNodeFactory(the_geom_linestring=None)

    geometry_check = GeometryCheck(models.ConnectionNode.the_geom_linestring)
    invalid_rows = geometry_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_type_check(session):
    factories.ConnectionNodeFactory.create_batch(
        2, the_geom="SRID=28992;POINT(-71.064544 42.28787)"
    )

    geometry_type_check = GeometryTypeCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_type_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_type_check_invalid_geom_type(session):
    if session.bind.name == "postgresql":
        pytest.skip("Not sure how to insert invalid geometry types in postgresql")
    factories.ConnectionNodeFactory(the_geom="SRID=28992;POINT(-71.064544 42.28787)")
    invalid_geom_type = factories.ConnectionNodeFactory(
        the_geom="SRID=28992;LINESTRING(71.0 42.2, 71.3 42.3)"
    )

    geometry_type_check = GeometryTypeCheck(models.ConnectionNode.the_geom)
    invalid_rows = geometry_type_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == invalid_geom_type.id


def test_enum_check(session):
    factories.BoundaryConditions2DFactory()

    enum_check = EnumCheck(models.BoundaryConditions2D.boundary_type)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 0


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
    if session.bind.name == "postgresql":
        pytest.skip(
            "Not able to add invalid aggregation method due to "
            "CHECKED CONSTRAINT"
        )
    a = factories.AggregationSettingsFactory(aggregation_method="invalid")

    enum_check = EnumCheck(models.AggregationSettings.aggregation_method)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == a.id


def test_sqlalchemy_to_sqlite_type_with_custom_type():
    customIntegerEnum = custom_types.IntegerEnum(constants.BoundaryType)
    assert _sqlalchemy_to_sqlite_type(customIntegerEnum) == "integer"


def test_conditional_checks(session):
    global_settings1 = factories.GlobalSettingsFactory(
        dem_obstacle_detection=True, dem_obstacle_height=-5
    )
    factories.GlobalSettingsFactory(
        dem_obstacle_detection=False, dem_obstacle_height=-5
    )

    query = Query(models.GlobalSetting).filter(
        models.GlobalSetting.dem_obstacle_height <= 0,
        models.GlobalSetting.dem_obstacle_detection == True
    )
    conditional_range_check_to_query_check = QueryCheck(
        column=models.GlobalSetting.dem_obstacle_height,
        invalid=query,
        message="GlobalSetting.dem_obstacle_height should be larger than 0 "
                "when GlobalSetting.dem_obstacle_height is True."
    )
    invalids_querycheck = conditional_range_check_to_query_check.get_invalid(session)
    assert len(invalids_querycheck) == 1
    assert invalids_querycheck[0].id == global_settings1.id


def test_conditional_check_storage_area(session):
    # if connection node is a manhole, then the storage area of the
    # connection_node must be > 0
    factories.ConnectionNodeFactory(storage_area=5)
    factories.ConnectionNodeFactory(storage_area=-3)
    conn_node_manhole_valid = factories.ConnectionNodeFactory(storage_area=4)
    conn_node_manhole_invalid = factories.ConnectionNodeFactory(storage_area=-5)
    factories.ManholeFactory(connection_node=conn_node_manhole_valid)
    factories.ManholeFactory(
        connection_node=conn_node_manhole_invalid
    )

    query = Query(models.ConnectionNode).join(
        models.Manhole
    ).filter(
        models.ConnectionNode.storage_area <= 0
    )
    query_check = QueryCheck(
        column=models.ConnectionNode.storage_area,
        invalid=query,
        message=""
    )

    invalids = query_check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == conn_node_manhole_invalid.id


def test_conditional_check_joining_criterion_valid(session):
    # Joining on criterion valid fails because it takes the complement (negation)
    # of the joins (instead of only the where statement (joins are in the where
    # statement)).
    connection_node1 = factories.ConnectionNodeFactory()
    connection_node2 = factories.ConnectionNodeFactory()
    manhole1 = factories.ManholeFactory(
        connection_node=connection_node1, bottom_level=1.0
    )
    factories.ManholeFactory(
        connection_node=connection_node2, bottom_level=-1.0
    )
    factories.PumpstationFactory(
        connection_node_start=connection_node1, lower_stop_level=0.0
    )
    factories.PumpstationFactory(
        connection_node_start=connection_node2, lower_stop_level=2.0
    )

    check_lower_stop_level_gt_bottom_level_compliment = GeneralCheck(
        column=models.Manhole.bottom_level,
        criterion_valid=and_(
            models.Pumpstation.connection_node_start_id == models.ConnectionNode.id,
            models.Manhole.connection_node_id == models.ConnectionNode.id,
            models.Pumpstation.lower_stop_level > models.Manhole.bottom_level,
        ),
    )
    invalids = check_lower_stop_level_gt_bottom_level_compliment.get_invalid(session)
    assert len(invalids) != 1  # Note that 1 is what we actually want!
    assert invalids[0].id == manhole1.id


def test_query_check_with_joins(session):
    connection_node1 = factories.ConnectionNodeFactory()
    connection_node2 = factories.ConnectionNodeFactory()
    factories.ManholeFactory(
        connection_node=connection_node1, bottom_level=1.0
    )
    factories.ManholeFactory(
        connection_node=connection_node2, bottom_level=-1.0
    )
    factories.PumpstationFactory(
        connection_node_start=connection_node1, lower_stop_level=0.0
    )
    factories.PumpstationFactory(
        connection_node_start=connection_node2, lower_stop_level=2.0
    )

    query = Query(models.ConnectionNode).join(
        models.Pumpstation.connection_node_start
    ).join(
        models.Manhole, models.ConnectionNode.id == models.Manhole.connection_node_id
    ).filter(
        models.Pumpstation.lower_stop_level <= models.Manhole.bottom_level,
    )
    check = QueryCheck(
        column=models.Manhole.bottom_level,
        invalid=query,
        message="Pumpstation.lower_stop_level should be higher than "
                "Manhole.bottom_level"
    )
    invalids = check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == connection_node1.id


def test_query_check_on_pumpstation(session):
    connection_node1 = factories.ConnectionNodeFactory()
    connection_node2 = factories.ConnectionNodeFactory()
    factories.ManholeFactory(
        connection_node=connection_node1, bottom_level=1.0
    )
    factories.ManholeFactory(
        connection_node=connection_node2, bottom_level=-1.0
    )
    pumpstation_wrong = factories.PumpstationFactory(
        connection_node_start=connection_node1, lower_stop_level=0.0
    )
    factories.PumpstationFactory(
        connection_node_start=connection_node2, lower_stop_level=2.0
    )

    query = Query(models.Pumpstation).join(
        models.ConnectionNode, models.Pumpstation.connection_node_start_id == models.ConnectionNode.id  # noqa: E501
    ).join(
        models.Manhole, models.Manhole.connection_node_id == models.ConnectionNode.id
    ).filter(
        models.Pumpstation.lower_stop_level <= models.Manhole.bottom_level,
    )
    check = QueryCheck(
        column=models.Pumpstation.lower_stop_level,
        invalid=query,
        message="Pumpstation lower_stop_level should be higher than Manhole "
                "bottom_level"
    )
    invalids = check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == pumpstation_wrong.id


def test_get_valid(session):
    factories.ConnectionNodeFactory(storage_area=1)
    factories.ConnectionNodeFactory(storage_area=2)
    factories.ConnectionNodeFactory(storage_area=3)

    range_check = GeneralCheck(
        column=models.ConnectionNode.storage_area,
        criterion_valid=models.ConnectionNode.storage_area > 2,
    )
    to_check = range_check.to_check(session).all()
    assert len(to_check) == 3
    invalids = range_check.get_invalid(session)
    valids = range_check.get_valid(session)
    assert len(valids) + len(invalids) == 3


def test_general_check_range(session):
    w1 = factories.WeirFactory(friction_value=2)
    factories.WeirFactory(friction_value=-1)

    invalid_criterion = models.Weir.friction_value > 0
    general_range_check = GeneralCheck(
        column=models.Weir.friction_value, criterion_invalid=invalid_criterion
    )

    invalid = general_range_check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == w1.id


def test_general_check_valid_criterion_range(session):
    factories.WeirFactory(friction_value=2)
    w2 = factories.WeirFactory(friction_value=-1)

    valid_criterion = models.Weir.friction_value >= 0
    general_range_check = GeneralCheck(
        column=models.Weir.friction_value, criterion_valid=valid_criterion
    )

    invalid = general_range_check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == w2.id


@pytest.mark.skip("Aggregate function not working for general checks")
def test_general_check_aggregation_function(session):
    # Aggregation functions need something different!

    w1 = factories.WeirFactory(friction_value=2)
    w2 = factories.WeirFactory(friction_value=-1)

    invalid_criterion = func.count(models.Weir.friction_value) < 3
    general_range_check = GeneralCheck(
        column=models.Weir.friction_value, criterion_invalid=invalid_criterion
    )

    invalid = general_range_check.get_invalid(session)
    assert len(invalid) == 2
    invalid_ids = [row.id for row in invalid]
    assert w1.id in invalid_ids
    assert w2.id in invalid_ids


def test_general_check_modulo_operator(session):
    factories.GlobalSettingsFactory(
        nr_timesteps=120, output_time_step=20
    )
    global_settings_remainder = factories.GlobalSettingsFactory(
        nr_timesteps=125, output_time_step=20  # This is a FLOAT
    )
    # We cast to Integer because postgis modulo operator expects two of
    # same type.

    modulo_check = GeneralCheck(
        column=models.GlobalSetting.nr_timesteps,
        criterion_valid=models.GlobalSetting.nr_timesteps
        % cast(models.GlobalSetting.output_time_step, Integer) == 0,
    )

    invalid = modulo_check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == global_settings_remainder.id


def test_query_check_manhole_drain_level_calc_type_2(session):
    # manhole.drain_level can be null, but if manhole.calculation_type == 2 (Connected)
    # then manhole.drain_level >= manhole.bottom_level
    factories.ManholeFactory(drain_level=None)
    factories.ManholeFactory(drain_level=1)
    m3_error = factories.ManholeFactory(
        drain_level=None,
        calculation_type=constants.CalculationTypeNode.CONNECTED
    )  # drain_level cannot be null when calculation_type is CONNECTED
    m4_error = factories.ManholeFactory(
        drain_level=1,
        bottom_level=2,
        calculation_type=constants.CalculationTypeNode.CONNECTED
    )  # bottom_level  >= drain_level when calculation_type is CONNECTED
    factories.ManholeFactory(
        drain_level=1,
        bottom_level=0,
        calculation_type=constants.CalculationTypeNode.CONNECTED
    )
    factories.ManholeFactory(
        drain_level=None,
        bottom_level=0,
        calculation_type=constants.CalculationTypeNode.EMBEDDED
    )

    query_drn_lvl_st_bttm_lvl = Query(models.Manhole).filter(
        models.Manhole.drain_level < models.Manhole.bottom_level,
        models.Manhole.calculation_type == constants.CalculationTypeNode.CONNECTED
    )
    query_invalid_not_null = Query(models.Manhole).filter(
        models.Manhole.calculation_type == constants.CalculationTypeNode.CONNECTED,
        models.Manhole.drain_level == None
    )
    check_drn_lvl_gt_bttm_lvl = QueryCheck(
        column=models.Manhole.bottom_level,
        invalid=query_drn_lvl_st_bttm_lvl,
        message="Manhole.drain_level >= Manhole.bottom_level when "
                "Manhole.calculation_type is CONNECTED"
    )
    check_invalid_not_null = QueryCheck(
        column=models.Manhole.drain_level,
        invalid=query_invalid_not_null,
        message="Manhole.drain_level cannot be null when Manhole.calculation_type is "
                "CONNECTED"
    )
    errors1 = check_drn_lvl_gt_bttm_lvl.get_invalid(session)
    errors2 = check_invalid_not_null.get_invalid(session)
    assert len(errors1) == 1
    assert len(errors2) == 1
    assert m3_error.id == errors2[0].id
    assert m4_error.id == errors1[0].id


def test_global_settings_no_use_1d_flow_and_1d_elements(session):
    factories.GlobalSettingsFactory(use_1d_flow=1)
    g2 = factories.GlobalSettingsFactory(use_1d_flow=0)
    factories.ConnectionNodeFactory.create_batch(3)

    query_1d_nodes_and_no_use_1d_flow = Query(models.GlobalSetting).filter(
        models.GlobalSetting.use_1d_flow == False,
        Query(func.count(models.ConnectionNode.id) > 0).label("1d_count")
    )
    check_use_1d_flow_has_1d = QueryCheck(
        column=models.GlobalSetting.use_1d_flow,
        invalid=query_1d_nodes_and_no_use_1d_flow,
        message="GlobalSettings.use_1d_flow must be set to True when there are 1d "
                "elements"
    )
    errors = check_use_1d_flow_has_1d.get_invalid(session)
    assert len(errors) == 1
    assert errors[0].id == g2.id


def test_global_settings_use_1d_flow_and_no_1d_elements(session):
    factories.GlobalSettingsFactory(use_1d_flow=1)
    factories.GlobalSettingsFactory(use_1d_flow=0)

    query_1d_nodes_and_no_use_1d_flow = Query(models.GlobalSetting).filter(
        models.GlobalSetting.use_1d_flow == False,
        Query(func.count(models.ConnectionNode.id) > 0).label("1d_count")
    )
    check_use_1d_flow_has_1d = QueryCheck(
        column=models.GlobalSetting.use_1d_flow,
        invalid=query_1d_nodes_and_no_use_1d_flow,
        message="GlobalSettings.use_1d_flow must be set to True when there are 1d "
                "elements"
    )
    errors = check_use_1d_flow_has_1d.get_invalid(session)
    assert len(errors) == 0


def test_global_settings_start_time(session):
    if session.bind.name == "postgresql":
        pytest.skip("Can't insert wrong datatype in postgres")
    factories.GlobalSettingsFactory(start_time='18:00:00')
    factories.GlobalSettingsFactory(start_time=None)
    wrong_start_time = factories.GlobalSettingsFactory(start_time='asdf18:00:00')

    check_start_time = QueryCheck(
        column=models.GlobalSetting.start_time,
        invalid=Query(models.GlobalSetting).filter(
            func.datetime(models.GlobalSetting.start_time) == None,
            models.GlobalSetting.start_time != None
        ),
        message="GlobalSettings.start_time is an invalid, make sure it has the "
                "following format: 'HH:MM:SS'"
    )

    errors = check_start_time.get_invalid(session)
    assert len(errors) == 1
    assert errors[0].id == wrong_start_time.id


def test_global_settings_start_date(session):
    if session.bind.name == "postgresql":
        pytest.skip("Can't insert wrong datatype in postgres")
    factories.GlobalSettingsFactory(start_date='1991-08-27')
    wrong_start_date = factories.GlobalSettingsFactory(start_date='asdf18:00:00')

    check_start_date = QueryCheck(
        column=models.GlobalSetting.start_date,
        invalid=Query(models.GlobalSetting).filter(
            func.date(models.GlobalSetting.start_date) == None,
            models.GlobalSetting.start_date != None
        ),
        message="GlobalSettings.start_date is an invalid, make sure it has the "
                "following format: 'YYYY-MM-DD'"
    )

    errors = check_start_date.get_invalid(session)
    assert len(errors) == 1
    assert errors[0].id == wrong_start_date.id
