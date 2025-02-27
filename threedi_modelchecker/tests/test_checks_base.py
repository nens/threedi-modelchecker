import factory
import pytest
from sqlalchemy import func
from sqlalchemy.orm import Query
from threedi_schema import constants, custom_types, models

from threedi_modelchecker.checks.base import (
    _sqlalchemy_to_sqlite_types,
    AllEqualCheck,
    EnumCheck,
    EPSGGeomCheck,
    ForeignKeyCheck,
    GeometryCheck,
    GeometryTypeCheck,
    ListOfIntsCheck,
    NotNullCheck,
    QueryCheck,
    RangeCheck,
    TypeCheck,
    UniqueCheck,
)

from . import factories


def test_base_extra_filters_ok(session):
    factories.ConnectionNodeFactory(id=1, storage_area=3.0)
    factories.ConnectionNodeFactory(id=2, storage_area=None)

    null_check = NotNullCheck(
        column=models.ConnectionNode.storage_area, filters=models.ConnectionNode.id != 2
    )
    invalid_rows = null_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_base_extra_filters_err(session):
    factories.ConnectionNodeFactory(id=1, storage_area=3.0)
    factories.ConnectionNodeFactory(id=2, storage_area=None)

    null_check = NotNullCheck(
        column=models.ConnectionNode.storage_area, filters=models.ConnectionNode.id == 2
    )
    invalid_rows = null_check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_fk_check(session):
    factories.ConnectionNodeFactory(id=1)
    factories.PumpFactory(connection_node_id=1)
    fk_check = ForeignKeyCheck(models.ConnectionNode.id, models.Pump.connection_node_id)
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_no_entries(session):
    fk_check = ForeignKeyCheck(models.ConnectionNode.id, models.Pump.connection_node_id)
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_null_fk(session):
    conn_node = factories.ConnectionNodeFactory(id=1)
    factories.PumpFactory.create_batch(5, connection_node_id=conn_node.id)
    factories.PumpFactory(connection_node_id=None)

    fk_check = ForeignKeyCheck(models.ConnectionNode.id, models.Pump.connection_node_id)
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_fk_check_missing_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ChannelFactory(connection_node_id_start=conn_node.id)
    missing_fk = factories.ChannelFactory(connection_node_id_start=-1)
    fk_check = ForeignKeyCheck(
        models.ConnectionNode.id, models.Channel.connection_node_id_start
    )
    invalid_rows = fk_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == missing_fk.id


def test_unique_check(session):
    factories.ChannelFactory.create_batch(5)
    unique_check = UniqueCheck(models.Channel.code)
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_unique_check_duplicate_value(session):
    channels = factories.ChannelFactory.create_batch(
        5, exchange_type=factory.Sequence(lambda n: n)
    )
    dup_channel = factories.ChannelFactory(exchange_type=channels[0].exchange_type)

    unique_check = UniqueCheck(models.Channel.exchange_type)
    invalid_rows = unique_check.get_invalid(session)

    assert len(invalid_rows) == 2
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert channels[0].id in invalid_ids
    assert dup_channel.id in invalid_ids


def test_unique_check_null_values(session):
    factories.ChannelFactory.create_batch(
        5, exchange_type=factory.Sequence(lambda n: n)
    )
    factories.ChannelFactory.create_batch(3, exchange_type=None)

    unique_check = UniqueCheck(models.Channel.exchange_type)
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_unique_check_multiple_columns(session):
    factories.AggregationSettingsFactory()
    factories.AggregationSettingsFactory(aggregation_method="sum")

    unique_check = UniqueCheck(
        (
            models.AggregationSettings.flow_variable,
            models.AggregationSettings.aggregation_method,
        )
    )
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_unique_check_multiple_columns_duplicate(session):
    factories.AggregationSettingsFactory()
    factories.AggregationSettingsFactory()

    unique_check = UniqueCheck(
        (
            models.AggregationSettings.flow_variable,
            models.AggregationSettings.aggregation_method,
        )
    )
    invalid_rows = unique_check.get_invalid(session)
    assert len(invalid_rows) == 2


def test_unique_check_multiple_description():
    unique_check = UniqueCheck(
        (
            models.AggregationSettings.flow_variable,
            models.AggregationSettings.aggregation_method,
        )
    )
    assert unique_check.description() == (
        "columns ['aggregation_method', 'flow_variable'] in table "
        "aggregation_settings should be unique together"
    )


def test_all_equal_check(session):
    factories.ModelSettingsFactory(minimum_table_step_size=0.5)
    factories.ModelSettingsFactory(minimum_table_step_size=0.5)
    check = AllEqualCheck(models.ModelSettings.minimum_table_step_size)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_all_equal_check_different_value(session):
    factories.ModelSettingsFactory(minimum_table_step_size=0.5)
    factories.ModelSettingsFactory(minimum_table_step_size=0.6)
    factories.ModelSettingsFactory(minimum_table_step_size=0.5)
    factories.ModelSettingsFactory(minimum_table_step_size=0.7)

    check = AllEqualCheck(models.ModelSettings.minimum_table_step_size)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 2
    assert invalid_rows[0].minimum_table_step_size == 0.6
    assert invalid_rows[1].minimum_table_step_size == 0.7


def test_all_equal_check_null_value(session):
    factories.ModelSettingsFactory(maximum_table_step_size=None)
    factories.ModelSettingsFactory(maximum_table_step_size=None)

    check = AllEqualCheck(models.ModelSettings.maximum_table_step_size)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_all_equal_check_null_value_different(session):
    factories.ModelSettingsFactory(maximum_table_step_size=1.0)
    factories.ModelSettingsFactory(maximum_table_step_size=None)

    check = AllEqualCheck(models.ModelSettings.maximum_table_step_size)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_all_equal_check_no_records(session):
    check = AllEqualCheck(models.ModelSettings.minimum_table_step_size)
    invalid_rows = check.get_invalid(session)
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


def test_threedi_db_and_factories(session):
    """Test to ensure that the threedi_db and factories use the same
    session object."""
    factories.ChannelFactory()
    q = session.query(models.Channel)
    assert q.count() == 1


def test_run_spatial_function(session):
    """Example how to use spatial functions.

    Works on postgis and spatialite"""
    factories.ConnectionNodeFactory()
    q = session.query(func.ST_AsGeoJSON(models.ConnectionNode.geom))
    q.first()


def test_type_check(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ChannelFactory(exchange_type=123)
    factories.ChannelFactory(exchange_type=456)

    type_check = TypeCheck(models.Channel.exchange_type)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_type_check_integer(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ChannelFactory(exchange_type=123)
    factories.ChannelFactory(exchange_type=None)
    m1 = factories.ChannelFactory(exchange_type="abc")
    m2 = factories.ChannelFactory(exchange_type=1.23)

    type_check = TypeCheck(models.Channel.exchange_type)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 2
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert m1.id in invalid_ids
    assert m2.id in invalid_ids


def test_type_check_float_can_store_integer(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ChannelFactory(calculation_point_distance=1.3)
    factories.ChannelFactory(calculation_point_distance=None)
    factories.ChannelFactory(calculation_point_distance=1)
    m1 = factories.ChannelFactory(exchange_type="abc")

    type_check = TypeCheck(models.Channel.exchange_type)
    invalid_rows = type_check.get_invalid(session)
    valid_rows = type_check.get_valid(session)

    assert len(valid_rows) == 3
    assert len(invalid_rows) == 1
    invalid_ids = [invalid.id for invalid in invalid_rows]
    assert m1.id in invalid_ids


def test_type_check_varchar(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ChannelFactory(code="abc")
    factories.ChannelFactory(code=123)

    type_check = TypeCheck(models.Channel.code)
    invalid_rows = type_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_type_check_boolean(session):
    if session.bind.name == "postgresql":
        pytest.skip("type checks not working on postgres")
    factories.ModelSettingsFactory(use_1d_flow=True)
    factories.ModelSettingsFactory(use_1d_flow=1)
    # factories.ModelSettingsFactory(use_1d_flow='true')
    # factories.ModelSettingsFactory(use_1d_flow='1')
    # factories.ModelSettingsFactory(use_1d_flow=1.0)

    type_check = TypeCheck(models.ModelSettings.use_1d_flow)
    invalid_rows = type_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_geometry_check(session):
    factories.ConnectionNodeFactory(geom=factories.DEFAULT_POINT)

    geometry_check = GeometryCheck(models.ConnectionNode.geom)
    invalid_rows = geometry_check.get_invalid(session)

    assert len(invalid_rows) == 0


def test_geometry_type_check(session):
    factories.ConnectionNodeFactory.create_batch(2, geom=factories.DEFAULT_POINT)

    geometry_type_check = GeometryTypeCheck(models.ConnectionNode.geom)
    invalid_rows = geometry_type_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_enum_check(session):
    factories.BoundaryConditions2DFactory()

    enum_check = EnumCheck(models.BoundaryConditions2D.type)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_enum_check_with_null_values(session):
    factories.CulvertFactory(exchange_type=None)

    enum_check = EnumCheck(models.Culvert.exchange_type)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_enum_check_with_invalid_value(session):
    factories.BoundaryConditions2DFactory()
    faulty_boundary = factories.BoundaryConditions2DFactory(type=-1)

    enum_check = EnumCheck(models.BoundaryConditions2D.type)
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
            "Not able to add invalid aggregation method due to " "CHECKED CONSTRAINT"
        )
    a = factories.AggregationSettingsFactory(aggregation_method="invalid")

    enum_check = EnumCheck(models.AggregationSettings.aggregation_method)
    invalid_rows = enum_check.get_invalid(session)
    assert len(invalid_rows) == 1
    assert invalid_rows[0].id == a.id


def test_sqlalchemy_to_sqlite_type_with_custom_type():
    customIntegerEnum = custom_types.IntegerEnum(constants.BoundaryType)
    assert _sqlalchemy_to_sqlite_types(customIntegerEnum) == ["integer"]


def test_conditional_checks(session):
    global_settings1 = factories.ModelSettingsFactory(minimum_cell_size=10)
    factories.ModelSettingsFactory(minimum_cell_size=20)

    query = Query(models.ModelSettings).filter(
        models.ModelSettings.minimum_cell_size < 20,
    )
    conditional_range_check_to_query_check = QueryCheck(
        column=models.ModelSettings.minimum_cell_size,
        invalid=query,
        message="ModelSettings.minimum_cell_size should be smaller than 20 ",
    )
    invalids_querycheck = conditional_range_check_to_query_check.get_invalid(session)
    assert len(invalids_querycheck) == 1
    assert invalids_querycheck[0].id == global_settings1.id


def test_conditional_check_storage_area(session):
    # if connection node is a manhole, then the storage area of the
    # connection_node must be > 0
    factories.ConnectionNodeFactory(storage_area=4)
    conn_node_manhole_invalid = factories.ConnectionNodeFactory(storage_area=-5)

    query = Query(models.ConnectionNode).filter(models.ConnectionNode.storage_area <= 0)
    query_check = QueryCheck(
        column=models.ConnectionNode.storage_area, invalid=query, message=""
    )

    invalids = query_check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == conn_node_manhole_invalid.id


def test_query_check_with_joins(session):
    connection_node1 = factories.ConnectionNodeFactory(id=1, bottom_level=1.0)
    connection_node2 = factories.ConnectionNodeFactory(id=2, bottom_level=-1.0)
    pump1 = factories.PumpFactory(
        connection_node_id=connection_node1.id, lower_stop_level=0.0
    )
    factories.PumpFactory(connection_node_id=connection_node2.id, lower_stop_level=0.0)
    factories.PumpFactory(connection_node_id=connection_node2.id, lower_stop_level=2.0)
    query = (
        Query(models.Pump)
        .join(
            models.ConnectionNode,
            models.Pump.connection_node_id == models.ConnectionNode.id,
        )
        .filter(
            models.Pump.lower_stop_level <= models.ConnectionNode.bottom_level,
        )
    )
    check = QueryCheck(
        column=models.Pump.lower_stop_level,
        invalid=query,
        message="Pump.lower_stop_level should be higher than "
        "ConnectionNode.bottom_level",
    )
    invalids = check.get_invalid(session)
    assert len(invalids) == 1
    assert invalids[0].id == pump1.id


def test_query_check_manhole_drain_level_calc_type_2(session):
    # ConnectionNodeFactory.exchange_level can be null, but if ConnectionNodeFactory.exchange_type == 2 (Connected)
    # then ConnectionNodeFactory.exchange_level >= ConnectionNodeFactory.bottom_level
    factories.ConnectionNodeFactory(exchange_level=None)
    factories.ConnectionNodeFactory(exchange_level=1)
    m3_error = factories.ConnectionNodeFactory(
        exchange_level=None, exchange_type=constants.CalculationTypeNode.CONNECTED
    )
    m4_error = factories.ConnectionNodeFactory(
        exchange_level=1,
        bottom_level=2,
        exchange_type=constants.CalculationTypeNode.CONNECTED,
    )  # bottom_level  >= drain_level when exchange_type is CONNECTED
    factories.ConnectionNodeFactory(
        exchange_level=1,
        bottom_level=0,
        exchange_type=constants.CalculationTypeNode.CONNECTED,
    )
    factories.ConnectionNodeFactory(
        exchange_level=None,
        bottom_level=0,
        exchange_type=constants.CalculationTypeNode.EMBEDDED,
    )

    query_drn_lvl_st_bttm_lvl = Query(models.ConnectionNode).filter(
        models.ConnectionNode.exchange_level < models.ConnectionNode.bottom_level,
        models.ConnectionNode.exchange_type == constants.CalculationTypeNode.CONNECTED,
    )
    query_invalid_not_null = Query(models.ConnectionNode).filter(
        models.ConnectionNode.exchange_type == constants.CalculationTypeNode.CONNECTED,
        models.ConnectionNode.exchange_level == None,
    )
    check_drn_lvl_gt_bttm_lvl = QueryCheck(
        column=models.ConnectionNode.bottom_level,
        invalid=query_drn_lvl_st_bttm_lvl,
        message="ConnectionNode.exhange_level >= ConnectionNode.bottom_level when "
        "ConnectionNode.exchange_type is CONNECTED",
    )
    check_invalid_not_null = QueryCheck(
        column=models.ConnectionNode.exchange_level,
        invalid=query_invalid_not_null,
        message="ConnectionNode.exchange_level cannot be null when ConnectionNode.exchange_type is "
        "CONNECTED",
    )
    errors1 = check_drn_lvl_gt_bttm_lvl.get_invalid(session)
    errors2 = check_invalid_not_null.get_invalid(session)
    assert len(errors1) == 1
    assert len(errors2) == 1
    assert m3_error.id == errors2[0].id
    assert m4_error.id == errors1[0].id


def test_global_settings_no_use_1d_flow_and_1d_elements(session):
    factories.ModelSettingsFactory(use_1d_flow=1)
    g2 = factories.ModelSettingsFactory(use_1d_flow=0)
    factories.ConnectionNodeFactory.create_batch(3)

    query_1d_nodes_and_no_use_1d_flow = Query(models.ModelSettings).filter(
        models.ModelSettings.use_1d_flow == False,
        Query(func.count(models.ConnectionNode.id) > 0).label("1d_count"),
    )
    check_use_1d_flow_has_1d = QueryCheck(
        column=models.ModelSettings.use_1d_flow,
        invalid=query_1d_nodes_and_no_use_1d_flow,
        message="ModelSettingss.use_1d_flow must be set to True when there are 1d "
        "elements",
    )
    errors = check_use_1d_flow_has_1d.get_invalid(session)
    assert len(errors) == 1
    assert errors[0].id == g2.id


def test_global_settings_use_1d_flow_and_no_1d_elements(session):
    factories.ModelSettingsFactory(use_1d_flow=1)
    factories.ModelSettingsFactory(use_1d_flow=0)

    query_1d_nodes_and_no_use_1d_flow = Query(models.ModelSettings).filter(
        models.ModelSettings.use_1d_flow == False,
        Query(func.count(models.ConnectionNode.id) > 0).label("1d_count"),
    )
    check_use_1d_flow_has_1d = QueryCheck(
        column=models.ModelSettings.use_1d_flow,
        invalid=query_1d_nodes_and_no_use_1d_flow,
        message="ModelSettingss.use_1d_flow must be set to True when there are 1d "
        "elements",
    )
    errors = check_use_1d_flow_has_1d.get_invalid(session)
    assert len(errors) == 0


@pytest.mark.parametrize(
    "min_value,max_value,left_inclusive,right_inclusive",
    [
        (0, 100, False, False),
        (0, 42, False, True),
        (42, 100, True, False),
        (None, 100, False, False),
        (0, None, False, False),
    ],
)
def test_range_check_valid(
    session, min_value, max_value, left_inclusive, right_inclusive
):
    factories.ConnectionNodeFactory(storage_area=42)

    check = RangeCheck(
        min_value,
        max_value,
        left_inclusive,
        right_inclusive,
        column=models.ConnectionNode.storage_area,
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize(
    "min_value,max_value,left_inclusive,right_inclusive,msg",
    [
        (0, 42, True, False, "{} is <0 and/or >=42"),
        (42, 100, False, True, "{} is <=42 and/or >100"),
        (None, 42, True, False, "{} is >=42"),
        (42, None, False, False, "{} is <=42"),
    ],
)
def test_range_check_invalid(
    session, min_value, max_value, left_inclusive, right_inclusive, msg
):
    factories.ConnectionNodeFactory(storage_area=42)

    check = RangeCheck(
        min_value,
        max_value,
        left_inclusive,
        right_inclusive,
        column=models.ConnectionNode.storage_area,
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1

    assert check.description() == msg.format("connection_node.storage_area")


@pytest.mark.parametrize(
    "tag_ids_string, nof_invalid_expected",
    [("1,2,3", 0), ("1.0,2,3", 1), ("foo,bar", 1)],
)
def test_list_of_inst_check(session, tag_ids_string, nof_invalid_expected):
    factories.DryWeatherFlowFactory(tags=tag_ids_string)
    check = ListOfIntsCheck(column=models.DryWeatherFlow.tags)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == nof_invalid_expected


@pytest.mark.parametrize(
    "ref_epsg, valid",
    [
        (28992, True),
        (4326, False),
        (None, True),  # skip check when there is no epsg
    ],
)
def test_epsg_geom_check(session, ref_epsg, valid):
    factories.ConnectionNodeFactory()
    session.model_checker_context.epsg_ref_code = ref_epsg
    session.model_checker_context.epsg_ref_name = "foo"
    check = EPSGGeomCheck(column=models.ConnectionNode.geom)
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid
