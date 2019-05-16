import os

import pytest

from threedi_modelchecker import exporters
from .conftest import data_dir
from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.threedi_model import models
from threedi_modelchecker.threedi_model.models import Base

from tests import Session


@pytest.fixture
def bergermeer_db():
    bergermeer_file = 'v2_bergermeer_renier.sqlite'
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


@pytest.fixture
def grotemarkt():
    grotemarkt_file = 'grotemarktstraat8sept.sqlite'
    grotemarkt_path = os.path.join(data_dir, grotemarkt_file)
    grotemarkt_settings = {
        'db_path': grotemarkt_path,
        'db_file': grotemarkt_file
    }
    db = ThreediDatabase(grotemarkt_settings, db_type='spatialite')

    engine = db.get_engine()
    # Base.prepare(engine, reflect=True)

    # Configure the scoped session
    Session.configure(bind=engine)

    return db


def test_parse_model(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    errors = mc.parse_model()
    exporters.print_errors(errors)
    print('done')


def test_parse_model_heugem(heugem):
    mc = ThreediModelChecker(heugem)
    errors = mc.parse_model()
    summary = exporters.summarize_type_errors(errors)
    print(summary)
    print('done')


def test_parse_model_grotemarkt(grotemarkt):
    mc = ThreediModelChecker(grotemarkt)
    errors = mc.parse_model()
    exporters.print_errors(errors)
    print('done')
