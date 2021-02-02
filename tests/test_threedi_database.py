from tests import factories
from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.threedi_model import models


def test_threedi_db_and_factories(threedi_db):
    """Test to ensure that the threedi_db and factories use the same
    session object."""
    session = threedi_db.session()
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


def test_threedi_db_check_connection(threedi_db):
    assert threedi_db.check_connection()


def test_threedi_db_create_schema():
    db = ThreediDatabase.spatialite(":memory:")
    db.create_schema()
    assert db.engine.table_names() is not None
