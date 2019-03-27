import os

import pytest

from .conftest import data_dir
from model_checker.threedi_database import ThreediDatabase
from model_checker.schema_checks import ThreediModelChecker
from model_checker.models import Base

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
    Base.prepare(engine, reflect=True)

    # Configure the scoped session
    Session.configure(bind=engine)

    return db


def test_threedi_model_checker(bergermeer_db):
    mc = ThreediModelChecker(bergermeer_db)
    missing_foreign_keys = mc.check_foreign_keys()
    print(missing_foreign_keys)
    print('done')
