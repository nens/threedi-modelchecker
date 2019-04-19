import os

import pytest

from .conftest import data_dir
from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.model_checks import ThreediModelChecker, query_invalid_type
from threedi_modelchecker import models
from threedi_modelchecker.models import Base

from tests import Session


@pytest.fixture
def bergermeer_db():
    bergermeer_file = 'v2_bergermeer.sqlite'
    bergermeer_path = os.path.join(data_dir, bergermeer_file)
    bergermeer_settings = {
        'db_path': bergermeer_path,
        'db_file': bergermeer_file
    }
    db = ThreediDatabase(bergermeer_settings, db_type='spatialite')

    engine = db.get_engine()
    # Base.prepare(engine, reflect=True)

    # Configure the scoped session
    Session.configure(bind=engine)

    return db


@pytest.fixture
def fryslan():
    fryslan_file = 'wf_zw_052.sqlite'
    fryslan_path = os.path.join(data_dir, fryslan_file)
    fryslan_settings = {
        'db_path': fryslan_path,
        'db_file': fryslan_file
    }
    db = ThreediDatabase(fryslan_settings, db_type='spatialite')

    engine = db.get_engine()
    # Base.prepare(engine, reflect=True)

    # Configure the scoped session
    Session.configure(bind=engine)

    return db


@pytest.fixture
def heugem():
    heugem_file = 'heugem_limmel_integraal_midden.sqlite'
    heugem_path = os.path.join(data_dir, heugem_file)
    heugem_settings = {
        'db_path': heugem_path,
        'db_file': heugem_file
    }
    db = ThreediDatabase(heugem_settings, db_type='spatialite')

    engine = db.get_engine()
    # Base.prepare(engine, reflect=True)

    # Configure the scoped session
    Session.configure(bind=engine)

    return db


def test_mc_foreign_keys(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    missing_foreign_keys = mc.check_foreign_keys()
    print(missing_foreign_keys)
    print('done')


def test_mc_check_not_null(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    error_columns = mc.check_not_null_columns()
    print(error_columns)


def test_get_null_column_errors(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    null_error_columns = mc.get_null_errors()
    for e in null_error_columns:
        print(e)


def test_mc_check_valid_type(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    error_columns = mc.check_data_types()
    from pprint import pprint
    print(len(error_columns))
    print(error_columns)


def test_type(bergermeer_db):
    session = bergermeer_db.get_session()

    r = query_invalid_type(session, models.Manhole.zoom_category)
    print(r)
    print('done')


def test_parse_model(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    mc.parse_model()
    print('done')


def test_parse_model_heugem(heugem):
    mc = ThreediModelChecker(heugem)
    mc.parse_model()
    print('done')
