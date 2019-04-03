import factory
import pytest

from model_checker.schema_checks import (
    ThreediModelChecker, check_foreign_key, check_unique, check_not_null,
    check_valid_type, get_none_nullable_columns, get_foreign_key_columns)
from model_checker import models
from tests import factories


def test_check_fk(session):
    factories.ManholeFactory.create_batch(5)

    r = check_foreign_key(
        session,
        models.Manhole.connection_node_id,
        models.ConnectionNode.id
    )
    assert len(r) == 0


def test_check_fk_no_entries(session):
    r = check_foreign_key(
        session,
        models.Manhole.connection_node_id,
        models.ConnectionNode.id
    )
    assert len(r) == 0


def test_check_fk_null_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    factories.ManholeFactory(manhole_indicator=None)

    r = check_foreign_key(
        session,
        models.Manhole.manhole_indicator,
        models.ConnectionNode.id
    )
    assert len(r) == 0


def test_check_fk_both_null(session):
    global_settings = factories.GlobalSettingsFactory(control_group_id=None)

    assert session.query(models.GlobalSetting).first().id is not None
    assert session.query(models.GlobalSetting.control_group_id).scalar() is None
    assert session.query(models.ControlGroup.id).scalar() is None
    r = check_foreign_key(
        session,
        models.GlobalSetting.control_group_id,
        models.ControlGroup.id
    )
    assert len(r) == 0


def test_check_fk_missing_fk(session):
    conn_node = factories.ConnectionNodeFactory()
    factories.ManholeFactory.create_batch(5, manhole_indicator=conn_node.id)
    missing_fk = factories.ManholeFactory(manhole_indicator=-1)

    r = check_foreign_key(
        session,
        models.Manhole.manhole_indicator,
        models.ConnectionNode.id
    )
    assert len(r) == 1
    assert r[0].id == missing_fk.id


def test_check_unique(session):
    factories.ManholeFactory.create_batch(5)

    r = check_unique(session, models.Manhole.code)
    assert len(r) == 0


def test_check_unique_duplicate_value(session):
    manholes = factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n))
    duplicate = factories.ManholeFactory(
        zoom_category=manholes[0].zoom_category)

    r = check_unique(session, models.Manhole.zoom_category)
    assert len(r) == 2
    # assert duplicate in r
    # assert manholes[0] in r


def test_check_unique_null_values(session):
    factories.ManholeFactory.create_batch(
        5, zoom_category=factory.Sequence(lambda n: n))
    factories.ManholeFactory.create_batch(3, zoom_category=None)

    r = check_unique(session, models.ConnectionNode.id)
    assert len(r) == 0


def test_not_null(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)

    r = check_not_null(session, models.ConnectionNode.storage_area)
    assert len(r) == 0


def test_not_null_null_value(session):
    factories.ConnectionNodeFactory.create_batch(
        5, storage_area=3.0)
    null_node = factories.ConnectionNodeFactory(storage_area=None)

    r = check_not_null(session, models.ConnectionNode.storage_area)
    assert len(r) == 1
    # assert null_node in r


def test_get_none_nullable_columns():
    not_null_columns = get_none_nullable_columns(models.Manhole.__table__)
    assert len(not_null_columns) == 3
    assert models.Manhole.id in not_null_columns
    assert models.Manhole.code in not_null_columns
    assert models.Manhole.display_name in not_null_columns


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
    print(r)


def test_check_valid_type(session):
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=456)

    r = check_valid_type(session, models.Manhole.zoom_category)
    assert len(r) == 0


def test_check_valid_type_integer(session):
    factories.ManholeFactory(zoom_category=123)
    factories.ManholeFactory(zoom_category=None)
    m1 = factories.ManholeFactory(zoom_category='abc')
    m2 = factories.ManholeFactory(zoom_category=1.23)

    r = check_valid_type(session, models.Manhole.zoom_category)
    assert len(r) == 2

    ids = list(map(lambda x: getattr(x, 'id'), r))
    assert m1.id in ids
    assert m2.id in ids


def test_check_valid_type_varchar(session):
    factories.ManholeFactory(code='abc')
    factories.ManholeFactory(code=123)

    r = check_valid_type(session, models.Manhole.code)
    assert len(r) == 0


def test_check_valid_type_boolean(session):
    g = factories.GlobalSettingsFactory(use_1d_flow=True)
    factories.GlobalSettingsFactory(use_1d_flow=1)
    # factories.GlobalSettingsFactory(use_1d_flow='true')
    # factories.GlobalSettingsFactory(use_1d_flow='1')
    # factories.GlobalSettingsFactory(use_1d_flow=1.0)

    r = check_valid_type(session, models.GlobalSetting.use_1d_flow)
    assert len(r) == 0


class TestThreediModelChecker(object):

    def test_check_not_null_columns(self, modelchecker):
        result = modelchecker.check_not_null_columns()
        print(result)

    def test_check_foreign_keys(self, modelchecker):
        result = modelchecker.check_foreign_keys()
        print(result)

    def test_check_data_types(self, modelchecker):
        result = modelchecker.check_data_types()
        print(result)


@pytest.mark.skip('')
def test_get_foreign_key_relation(threedi_db):
    mc = ThreediModelChecker(threedi_db)
    tables = [
        models.Manhole.__table__,
        # models.ConnectionNode,
        # models.Weir
    ]
    session = threedi_db.get_session()
    not_null_columns = mc.get_not_null_columns(tables)

    column = not_null_columns[0]

    session.query(column.table).filter(column == None)

    check_not_null(session, not_null_columns[1])

    foreign_keys = mc.get_foreign_key_relations(tables)

    session = threedi_db.get_session()

    fk = foreign_keys[0]
    fk.target_fullname
    fk.column
    check_foreign_key(
        threedi_db.get_session(),
        foreign_keys[0].column,
    )


@pytest.mark.skip('')
def test_generate_foreign_key_checks(threedi_db):
    mc = ThreediModelChecker(threedi_db)
    mc.generate_foreign_key_checks()
