import factory
import pytest

from model_checker.schema_checks import (
    ThreediModelChecker, check_foreign_key, check_unique, check_not_null)
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
    global_settings = factories.GlobalSettingsFactory()

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
    assert r[0] is missing_fk


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
    assert duplicate in r
    assert manholes[0] in r


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
    assert null_node in r
