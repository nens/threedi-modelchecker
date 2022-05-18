from geoalchemy2 import func as geo_func
from threedi_modelchecker.spatialite_versions import get_spatialite_version, copy_model
from threedi_modelchecker.threedi_model import models
from threedi_modelchecker.errors import UpgradeFailedError

import pytest

def test_get_spatialite_version(empty_sqlite_v3):
    lib_version, file_version = get_spatialite_version(empty_sqlite_v3)
    assert lib_version in (3, 4, 5)
    assert file_version == 3


def test_copy_model(empty_sqlite_v3, empty_sqlite_v3_clone):
    obj = models.ConnectionNode(
        id=3, code="test", the_geom="SRID=4326;POINT(-71.064544 42.287870)"
    )
    with empty_sqlite_v3.session_scope() as session:
        session.add(obj)
        session.commit()

    copy_model(empty_sqlite_v3, empty_sqlite_v3_clone, models.ConnectionNode)

    with empty_sqlite_v3_clone.session_scope() as session:
        records = list(
            session.query(
                models.ConnectionNode.id,
                models.ConnectionNode.code,
                geo_func.ST_AsText(models.ConnectionNode.the_geom),
                models.ConnectionNode.the_geom_linestring,
            )
        )

        assert records == [(3, "test", "POINT(-71.064544 42.28787)", None)]


def test_copy_invalid_geometry(empty_sqlite_v3, empty_sqlite_v3_clone):
    """Copying an invalid geometry (ST_IsValid evaluates to False) is possible
    """
    obj = models.Surface(
        id=3, code="test", display_name="test", the_geom="SRID=4326;POLYGON((0 0, 10 10, 0 10, 10 0, 0 0))"
    )
    with empty_sqlite_v3.session_scope() as session:
        session.add(obj)
        session.commit()

    copy_model(empty_sqlite_v3, empty_sqlite_v3_clone, models.Surface)

    with empty_sqlite_v3_clone.session_scope() as session:
        records = list(
            session.query(
                models.Surface.id,
                geo_func.ST_AsText(models.Surface.the_geom),
            )
        )

        assert records == [(3, "POLYGON((0 0, 10 10, 0 10, 10 0, 0 0))")]



def test_copy_violates_null_constraint(empty_sqlite_v3, empty_sqlite_v3_clone):
    """Copying an invalid geometry (ST_IsValid evaluates to False) is possible
    """
    obj = models.Manhole(
        id=3, code="test", display_name="test"
    )
    with empty_sqlite_v3.session_scope() as session:
        session.execute()
        session.add(obj)
        session.commit()

    with pytest.raises(UpgradeFailedError):
        copy_model(empty_sqlite_v3, empty_sqlite_v3_clone, models.Manhole)
