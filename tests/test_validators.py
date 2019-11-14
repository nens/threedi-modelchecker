from geoalchemy2 import func

from threedi_modelchecker.threedi_model import models
from threedi_modelchecker.threedi_model import validators
from .factories import LeveeFactory, ManholeFactory


def test_get_schema():
    print(validators.Levee.schema())


def test_get_schema_json():
    print(validators.Levee.schema_json(indent=2))


def test_get_schema_json_relation():
    print(validators.GlobalSetting.schema_json(indent=2))


def test_levee_validator():
    levee = validators.Levee(
        id=1,
        code='my_code',
        crest_level=10.0,
        material=1,
        max_breach_depth='1.0'
    )
    print(levee)


def test_levee_from_db(session):
    LeveeFactory.create_batch(2)

    levee = session.query(models.Levee).first()
    # levee = session.query(func.AsEWKT(models.Levee.the_geom)).first()

    levee_validated = validators.Levee.from_orm(levee)
    print(levee_validated)


def test_relation(session):
    ManholeFactory()

    manhole = session.query(models.Manhole).first()
    manhole_validated = validators.Manhole.from_orm(manhole)
    print(manhole_validated)
