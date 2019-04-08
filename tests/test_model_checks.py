import factory
import pytest

from model_checker.model_checks import (
    ThreediModelChecker, query_missing_foreign_key, query_not_unique, query_not_null,
    query_invalid_type, get_none_nullable_columns, get_unique_columns,
    get_foreign_key_columns, get_null_errors)
from model_checker import models
from tests import factories


def test_check_fk(session):
    factories.ManholeFactory.create_batch(5)

    foreign_key_q = query_missing_foreign_key(
        session,
        models.Manhole.connection_node_id,
        models.ConnectionNode.id
    )
    assert foreign_key_q.count() == 0


def test_check_fk_no_entries(session):
    foreign_key_q = query_missing_foreign_key(
        session,
        models.Manhole.connection_node_id,
        models.ConnectionNode.id
    )
    assert foreign_key_q.count() == 0


def test_check_fk_null_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    factories.ManholeFactory(manhole_indicator=None)

    foreign_key_q = query_missing_foreign_key(
        session,
        models.Manhole.manhole_indicator,
        models.ConnectionNode.id
    )
    assert foreign_key_q.count() == 0


def test_check_fk_both_null(session):
    global_settings = factories.GlobalSettingsFactory(control_group_id=None)

    assert session.query(models.GlobalSetting).first().id is not None
    assert session.query(models.GlobalSetting.control_group_id).scalar() is None
    assert session.query(models.ControlGroup.id).scalar() is None
    foreign_key_q = query_missing_foreign_key(
        session,
        models.GlobalSetting.control_group_id,
        models.ControlGroup.id
    )
    assert foreign_key_q.count() == 0


def test_check_fk_missing_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    missing_fk = factories.ManholeFactory(manhole_indicator=-1)

    foreign_key_q = query_missing_foreign_key(
        session,
        models.Manhole.manhole_indicator,
        models.ConnectionNode.id
    )
    assert foreign_key_q.count() == 1
    assert foreign_key_q.first().id == missing_fk.id


def test_check_unique(session):
    factories.ManholeFactory.create_batch(5)

    not_unique_q = query_not_unique(session, models.Manhole.code)
    assert not_unique_q.count() == 0


def test_check_unique_duplicate_value(session):
    manholes = factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n))
    duplicate_manhole = factories.ManholeFactory(
        zoom_category=manholes[0].zoom_category)

    not_unique_q = query_not_unique(session, models.Manhole.zoom_category)
    assert not_unique_q.count() == 2
    not_unique_q_ids = list(not_unique_q.values('id'))
    unpacked_ids = [id for id, in not_unique_q_ids]
    assert manholes[0].id in unpacked_ids
    assert duplicate_manhole.id in unpacked_ids


def test_check_unique_null_values(session):
    factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n))
    factories.ManholeFactory.create_batch(3, zoom_category=None)

    not_unique_q = query_not_unique(session, models.ConnectionNode.id)
    assert not_unique_q.count() == 0


def test_not_null(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)

    not_null_q = query_not_null(session, models.ConnectionNode.storage_area)
    assert not_null_q.count() == 0


def test_not_null_with_null_value(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)
    null_node = factories.ConnectionNodeFactory(storage_area=None)

    not_null_q = query_not_null(session, models.ConnectionNode.storage_area)
    assert not_null_q.count() == 1
    assert not_null_q.first().id == null_node.id


def test_get_not_null_errors(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)
    null_node = factories.ConnectionNodeFactory(storage_area=None)

    errors = get_null_errors(
        session, models.ConnectionNode.__table__.c.storage_area)
    error_list = list(errors)
    # assert len(r) == 1
    # assert null_node in r


def test_get_none_nullable_columns():
    not_null_columns = get_none_nullable_columns(models.Manhole.__table__)
    assert len(not_null_columns) == 3
    assert models.Manhole.id in not_null_columns
    assert models.Manhole.code in not_null_columns
    assert models.Manhole.display_name in not_null_columns


def test_get_unique_columns():
    unique_columns = get_unique_columns(models.Manhole.__table__)
    assert len(unique_columns) == 1
    assert models.Manhole.id in unique_columns
    assert models.Manhole.connection_node_id


def test_get_foreign_key_columns():
    foreign_key_columns = get_foreign_key_columns(models.Manhole.__table__)
    assert len(foreign_key_columns) == 1
    fk = foreign_key_columns.pop()
    assert models.Manhole.connection_node_id == fk.parent
    assert models.ConnectionNode.id == fk.column


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


def test_check_valid_type(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=456)

    invalid_types_q = query_invalid_type(session, models.Manhole.zoom_category)
    assert invalid_types_q.count() == 0


def test_check_valid_type_integer(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=None)
    m1 = factories.ManholeFactory(zoom_category='abc')
    m2 = factories.ManholeFactory(zoom_category=1.23)

    invalid_types_q = query_invalid_type(session, models.Manhole.zoom_category)
    assert invalid_types_q.count() == 2
    invalid_type_ids = invalid_types_q.values('id')
    unpacked_ids = [id for id, in invalid_type_ids]
    assert m1.id in unpacked_ids
    assert m2.id in unpacked_ids


def test_check_valid_type_varchar(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.ManholeFactory(code='abc')
    factories.ManholeFactory(code=123)

    invalid_type_q = query_invalid_type(session, models.Manhole.code)
    assert invalid_type_q.count() == 0


def test_check_valid_type_boolean(session):
    if session.bind.name == 'postgresql':
        pytest.skip('type checks not working on postgres')
    factories.GlobalSettingsFactory(use_1d_flow=True)
    factories.GlobalSettingsFactory(use_1d_flow=1)
    # factories.GlobalSettingsFactory(use_1d_flow='true')
    # factories.GlobalSettingsFactory(use_1d_flow='1')
    # factories.GlobalSettingsFactory(use_1d_flow=1.0)

    invalid_type_q = query_invalid_type(session, models.GlobalSetting.use_1d_flow)
    assert invalid_type_q.count() == 0


class TestThreediModelChecker(object):

    def test_not_null_columns_errors(self, modelchecker):
        result = modelchecker.yield_null_errors()
        print(result)

    def test_foreign_keys_errors(self, modelchecker):
        result = modelchecker.yield_foreign_key_errors()
        print(result)

    def test_data_types_errors(self, modelchecker):
        result = modelchecker.yield_data_type_errors()
        print(result)

    def test_not_unique_errors(self, modelchecker):
        result = modelchecker.yield_not_unique_errors()
        print(result)

    def test_parse_model(self, modelchecker):
        all_errors = modelchecker.parse_model()
        print(all_errors)
