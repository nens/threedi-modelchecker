import os

import pytest

from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.model_checks import ThreediModelChecker
from tests import Session


CURRENT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(CURRENT_DIR, "data")
EMPTY_SQLITE_PATH = os.path.join(DATA_DIR, "empty.sqlite")
POSTGIS_SETTINGS = {
    "host": "postgis",
    "port": 5432,
    "database": "postgis",
    "username": "postgis",
    "password": "mysecret",
}


@pytest.fixture(
    scope="function",
    params=[("spatialite", EMPTY_SQLITE_PATH), ("postgres", POSTGIS_SETTINGS)],
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
    if request.param[0] == 'spatialite':
        db = ThreediDatabase.spatialite(request.param[1])
    else:
        db = ThreediDatabase.postgis(**request.param[1])

    Session.configure(bind=db.engine)

    # monkey-patch get_session
    db.session = lambda: Session()

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
    yield s
    # Rollback the session => no changes to the database
    s.rollback()
    # Remove it, so that the next test gets a new Session()
    Session.remove()


@pytest.fixture
def modelchecker(threedi_db):
    mc = ThreediModelChecker(threedi_db)
    return mc
