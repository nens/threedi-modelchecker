import os
import shutil

import pytest
from sqlalchemy import orm

from model_checker.models import Base
from model_checker.threedi_database import ThreediDatabase
from model_checker.model_checks import ThreediModelChecker

from tests import Session


cur_dir = os.path.dirname(__file__)
data_dir = os.path.join(cur_dir, 'data')
# Sqlite
emtpy_sqlite_file = 'empty.sqlite'
emtpy_sqlite_path = os.path.join(data_dir, emtpy_sqlite_file)
sqlite_settings = {
    'db_path': emtpy_sqlite_path,
    'db_file': emtpy_sqlite_file
}
# postgres
empty_postgres_file = 'empty.postgres'
empty_postgres_path = os.path.join(data_dir, empty_postgres_file)
postgis_settings = {
    'host': 'postgis',
    'port': 5432,
    'database': 'postgis',
    'username': 'postgis',
    'password': 'mysecret'
}


@pytest.fixture(scope='module')
def emtpy_spatialite_model(tmpdir):
    """Creates a temporarily empty-sqlite file with the threedi-model schema

    Returns the file path of the sqlite file."""
    emtpy_model_file = tmpdir.join('model.sqlite')
    shutil.copyfile(emtpy_sqlite_file, emtpy_model_file)
    return emtpy_model_file


@pytest.fixture(scope='module')
def empty_postgis_model():
    # connect to a postgres server
    # create an empty work_db based on pg_dump.
    # return connection-details (host/port/db-name/user/password)
    # Should clean up after use...
    yield {} # settings
    # teardown
    pass


def test_make_empty_postgres():
    pass


@pytest.fixture(
    scope='session',
    params=[('spatialite', sqlite_settings),
            ('postgres', postgis_settings)],
    ids=['spatialite', 'postgis'])
def threedi_db(request):
    db = ThreediDatabase(request.param[1], db_type=request.param[0],
                         echo=False)
    engine = db.get_engine()
    # Base.prepare(engine, reflect=True)

    # Configure the scoped session
    Session.configure(bind=engine)

    # monkey-patch get_session
    db.get_session = lambda: Session()

    yield db
    Session.remove()


@pytest.fixture
def session(threedi_db):
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


def test_connection(threedi_db):
    s = threedi_db.get_session()
    threedi_db.get_engine().connect()


def test_query_object(session):
    from model_checker.models import Levee
    levee = session.query(Levee).first()
    print('done')
