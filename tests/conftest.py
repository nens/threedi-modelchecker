from tests import Session
from threedi_modelchecker.model_checks import Context
from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.threedi_database import ThreediDatabase

import os
import pytest
import shutil


try:
    import psycopg2
except ImportError:
    psycopg2 = None

cur_dir = os.path.dirname(__file__)
data_dir = os.path.join(cur_dir, "data")
# Sqlite
emtpy_sqlite_file = "empty.sqlite"
emtpy_sqlite_path = os.path.join(data_dir, emtpy_sqlite_file)
sqlite_settings = {"db_path": emtpy_sqlite_path, "db_file": emtpy_sqlite_file}
# postgres
postgis_settings = {
    "host": "localhost",
    "port": 5432,
    "database": "postgis",
    "username": "postgis",
    "password": "mysecret",
}


@pytest.fixture(
    scope="function",
    params=[("spatialite", sqlite_settings), ("postgres", postgis_settings)],
    ids=["spatialite", "postgis"],
)
def threedi_db(request):
    """Fixture which yields a empty 3di database

    Fixture is parameterized to yield two types of databases: a postgis and a
    spatialite database.

    A global Session object is configured based on database type. This allows
    the factories to operate on the same session object. See:
    https://factoryboy.readthedocs.io/en/latest/orms.html#managing-sessions
    """
    if request.param[0] == "postgres" and psycopg2 is None:
        pytest.skip("Skipping postgres test as psycopg2 is not available.")

    db = ThreediDatabase(request.param[1], db_type=request.param[0], echo=False)
    engine = db.get_engine()
    Session.configure(bind=engine)

    # monkey-patch get_session
    db.get_session = lambda: Session()

    yield db
    Session.remove()


@pytest.fixture
def session(threedi_db):
    """Fixture which yields a session to an empty 3di database.

    At the end of the test, all uncommitted changes are rolled back. Never
    commit any transactions to the session! This will persist the changes
    and affect the upcoming tests.

    :return: sqlalchemy.orm.session.Session
    """
    s = Session()
    s.model_checker_context = Context()
    yield s
    # Rollback the session => no changes to the database
    s.rollback()
    # Remove it, so that the next test gets a new Session()
    Session.remove()


@pytest.fixture
def modelchecker(threedi_db):
    mc = ThreediModelChecker(threedi_db)
    return mc


@pytest.fixture
def in_memory_sqlite():
    """An in-memory database without a schema (to test schema migrations)"""
    return ThreediDatabase({"db_path": ""}, db_type="spatialite", echo=False)


@pytest.fixture
def south_latest_sqlite(tmp_path):
    """An empty SQLite that is in its latest South migration state"""
    tmp_sqlite = tmp_path / "south_latest.sqlite"
    shutil.copyfile(os.path.join(data_dir, "south_latest.sqlite"), tmp_sqlite)
    return ThreediDatabase({"db_path": tmp_sqlite}, db_type="spatialite", echo=False)


@pytest.fixture
def oldest_sqlite(tmp_path):
    """A real SQLite that is in its oldest possible south migration state (160)"""
    tmp_sqlite = tmp_path / "noordpolder.sqlite"
    shutil.copyfile(os.path.join(data_dir, "noordpolder.sqlite"), tmp_sqlite)
    return ThreediDatabase({"db_path": tmp_sqlite}, db_type="spatialite", echo=False)
