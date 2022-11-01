from . import factories
from threedi_modelchecker.model_checks import Context
from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.schema import ModelSchema
from threedi_modelchecker.threedi_database import ThreediDatabase

import pathlib
import pytest
import shutil


data_dir = pathlib.Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def threedi_db(tmpdir_factory):
    """Fixture which yields a empty 3di database

    A global Session object is configured based on database type. This allows
    the factories to operate on the same session object. See:
    https://factoryboy.readthedocs.io/en/latest/orms.html#managing-sessions
    """
    tmp_path = tmpdir_factory.mktemp("spatialite4")
    tmp_sqlite = tmp_path / "empty_v4.sqlite"
    shutil.copyfile(data_dir / "empty_v4.sqlite", tmp_sqlite)
    db = ThreediDatabase(tmp_sqlite)
    schema = ModelSchema(db)
    schema.upgrade(backup=False, upgrade_spatialite_version=False)
    schema.set_spatial_indexes()
    return db


@pytest.fixture(scope="session")
def gpkg_db(tmpdir_factory):
    tmp_path = tmpdir_factory.mktemp("noordpolder")
    tmp = tmp_path / "noordpolder.gpkg"
    shutil.copyfile(data_dir / "noordpolder.gpkg", tmp)
    return ThreediDatabase(tmp)


@pytest.fixture
def session(threedi_db):
    """Fixture which yields a session to an empty 3di database.

    At the end of the test, all uncommitted changes are rolled back. Never
    commit any transactions to the session! This will persist the changes
    and affect the upcoming tests.

    :return: sqlalchemy.orm.session.Session
    """
    s = threedi_db.get_session()

    factories.inject_session(s)
    s.model_checker_context = Context()

    yield s
    # Rollback the session => no changes to the database
    s.rollback()
    factories.inject_session(None)


@pytest.fixture
def modelchecker(threedi_db):
    mc = ThreediModelChecker(threedi_db)
    return mc


@pytest.fixture
def in_memory_sqlite():
    """An in-memory database without a schema (to test schema migrations)"""
    return ThreediDatabase("")


@pytest.fixture
def empty_sqlite_v3(tmp_path):
    """A function-scoped empty spatialite v3 in the latest migration state"""
    tmp_sqlite = tmp_path / "empty_v3.sqlite"
    shutil.copyfile(data_dir / "empty_v3.sqlite", tmp_sqlite)
    return ThreediDatabase(tmp_sqlite)


@pytest.fixture
def empty_sqlite_v4(tmp_path):
    """An function-scoped empty spatialite v4 in the latest migration state"""
    tmp_sqlite = tmp_path / "empty_v4.sqlite"
    shutil.copyfile(data_dir / "empty_v4.sqlite", tmp_sqlite)
    return ThreediDatabase(tmp_sqlite)


@pytest.fixture
def south_latest_sqlite(tmp_path):
    """An empty SQLite that is in its latest South migration state"""
    tmp_sqlite = tmp_path / "south_latest.sqlite"
    shutil.copyfile(data_dir / "south_latest.sqlite", tmp_sqlite)
    return ThreediDatabase(tmp_sqlite)


@pytest.fixture
def oldest_sqlite(tmp_path):
    """A real SQLite that is in its oldest possible south migration state (160)"""
    tmp_sqlite = tmp_path / "noordpolder.sqlite"
    shutil.copyfile(data_dir / "noordpolder.sqlite", tmp_sqlite)
    return ThreediDatabase(tmp_sqlite)
