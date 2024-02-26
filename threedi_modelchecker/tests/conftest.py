import pathlib
import shutil

import pytest
from threedi_schema import ModelSchema, ThreediDatabase

from threedi_modelchecker.checks.raster import LocalContext

from . import factories

data_dir = pathlib.Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def threedi_db(tmpdir_factory):
    """Fixture which yields a empty 3di database

    A global Session object is configured based on database type. This allows
    the factories to operate on the same session object. See:
    https://factoryboy.readthedocs.io/en/latest/orms.html#managing-sessions
    """
    tmp_path = tmpdir_factory.mktemp("spatialite4")
    tmp_sqlite = tmp_path / "empty.gpkg"
    shutil.copyfile(data_dir / "empty.gpkg", tmp_sqlite)
    db = ThreediDatabase(tmp_sqlite)
    schema = ModelSchema(db)
    schema.upgrade(backup=False, upgrade_spatialite_version=False)
    schema.set_spatial_indexes()
    return db


@pytest.fixture
def session(threedi_db):
    """Fixture which yields a session to an empty 3di database.

    At the end of the test, all uncommitted changes are rolled back. Never
    commit any transactions to the session! This will persist the changes
    and affect the upcoming tests.

    :return: sqlalchemy.orm.session.Session
    """
    s = threedi_db.get_session(future=True)

    factories.inject_session(s)
    s.model_checker_context = LocalContext(base_path=data_dir)

    yield s
    # Rollback the session => no changes to the database
    s.rollback()
    factories.inject_session(None)


@pytest.fixture
def empty_sqlite_v4(tmp_path):
    """An function-scoped empty geopackage v4 in the latest migration state"""
    tmp_sqlite = tmp_path / "empty.gpkg"
    shutil.copyfile(data_dir / "empty.gpkg", tmp_sqlite)
    return ThreediDatabase(tmp_sqlite)
