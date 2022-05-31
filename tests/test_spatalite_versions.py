from geoalchemy2 import func as geo_func
from threedi_modelchecker.spatialite_versions import copy_model
from threedi_modelchecker.spatialite_versions import get_spatialite_version
from threedi_modelchecker.threedi_model import models


def test_get_spatialite_version(empty_sqlite_v3):
    lib_version, file_version = get_spatialite_version(empty_sqlite_v3)
    assert lib_version in (3, 4, 5)
    assert file_version == 3


def test_copy_model(empty_sqlite_v3, empty_sqlite_v4):
    db_from = empty_sqlite_v3
    db_to = empty_sqlite_v4

    # Add a record to 'db_from'
    obj = models.ConnectionNode(
        id=3, code="test", the_geom="SRID=4326;POINT(-71.064544 42.287870)"
    )
    with db_from.session_scope() as session:
        session.add(obj)
        session.commit()

    # Copy it
    copy_model(db_from, db_to, models.ConnectionNode)

    # Check if it is present in 'db_to'
    with db_to.session_scope() as session:
        records = list(
            session.query(
                models.ConnectionNode.id,
                models.ConnectionNode.code,
                geo_func.ST_AsText(models.ConnectionNode.the_geom),
                models.ConnectionNode.the_geom_linestring,
            )
        )

        assert records == [(3, "test", "POINT(-71.064544 42.28787)", None)]


def test_copy_invalid_geometry(empty_sqlite_v3, empty_sqlite_v4):
    """Copying an invalid geometry (ST_IsValid evaluates to False) is possible"""
    db_from = empty_sqlite_v3
    db_to = empty_sqlite_v4

    obj = models.Surface(
        id=3,
        code="test",
        display_name="test",
        the_geom="SRID=4326;POLYGON((0 0, 10 10, 0 10, 10 0, 0 0))",
        surface_parameters_id=1,
    )
    with db_from.session_scope() as session:
        session.add(obj)
        session.commit()

    copy_model(db_from, db_to, models.Surface)

    with db_to.session_scope() as session:
        records = list(
            session.query(
                models.Surface.id,
                geo_func.ST_AsText(models.Surface.the_geom),
            )
        )

        assert records == [(3, "POLYGON((0 0, 10 10, 0 10, 10 0, 0 0))")]
