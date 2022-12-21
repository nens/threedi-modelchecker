from importlib.machinery import SourceFileLoader
from pathlib import Path
from threedi_modelchecker import ThreediDatabase
from threedi_modelchecker.schema import ModelSchema

import pytest
import threedi_modelchecker


path = (
    Path(threedi_modelchecker.__file__).parent
    / "migrations"
    / "versions"
    / "0213_connected_points_to_breaches.py"
)
migration_213 = SourceFileLoader("migration_213", str(path)).load_module(
    "migration_213"
)

CalculationPoint = migration_213.CalculationPoint
ConnectedPoint = migration_213.ConnectedPoint
Levee = migration_213.Levee
PotentialBreach = migration_213.PotentialBreach


@pytest.fixture
def in_memory_sqlite():
    """An in-memory database with the most recent schema"""
    db = ThreediDatabase("")
    ModelSchema(db).upgrade("0212", backup=False, set_views=False)
    return db


@pytest.fixture
def session(in_memory_sqlite):
    return in_memory_sqlite.get_session()


GEOM1 = "SRID=4326;POINT (0 0)"
GEOM2 = "SRID=4326;POINT (0 1)"
LINE = "SRID=4326;LINESTRING(0 0,0 1)"


@pytest.mark.parametrize(
    "objs",
    [
        [CalculationPoint(id=1, the_geom=GEOM1)],
        [ConnectedPoint(id=1, the_geom=GEOM1, calculation_pnt_id=None)],
        [ConnectedPoint(id=1, the_geom=GEOM1, calculation_pnt_id=1)],
        [
            CalculationPoint(id=1, the_geom=GEOM1),
            ConnectedPoint(id=1, the_geom=GEOM1, calculation_pnt_id=1),
        ],
        [
            CalculationPoint(id=1, the_geom=GEOM1),
            ConnectedPoint(id=1, the_geom=GEOM1, calculation_pnt_id=1),
            ConnectedPoint(id=2, the_geom=GEOM1, calculation_pnt_id=1),
        ],
    ],
)
def test_clean_connected_points(session, objs):
    session.add_all(objs)
    session.flush()
    migration_213.clean_connected_points(session)
    assert session.query(CalculationPoint).count() == 0
    assert session.query(ConnectedPoint).count() == 0


@pytest.mark.parametrize(
    "objs",
    [
        [
            CalculationPoint(id=1, the_geom=GEOM1),
            ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
        ],
        [
            CalculationPoint(id=1, the_geom=GEOM1),
            ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
            ConnectedPoint(id=2, the_geom=GEOM2, calculation_pnt_id=1),
        ],
    ],
)
def test_clean_connected_points_keep(session, objs):
    session.add_all(objs)
    session.flush()
    migration_213.clean_connected_points(session)

    actual = (
        session.query(CalculationPoint).count() + session.query(ConnectedPoint).count()
    )
    assert actual == len(objs)


def todict(x):
    return {col.name: getattr(x, col.name) for col in x.__table__.columns}


def assert_sqlalchemy_objects_equal(a, b):
    assert a.__class__ is b.__class__
    assert todict(a) == todict(b)


@pytest.mark.parametrize(
    "objs,expected",
    [
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
            ],
            PotentialBreach(id=1, channel_id=4, the_geom=LINE),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(
                    id=1, the_geom=GEOM2, calculation_pnt_id=1, exchange_level=1.1
                ),
            ],
            PotentialBreach(id=1, channel_id=4, the_geom=LINE, exchange_level=1.1),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1, levee_id=4),
                Levee(id=4, crest_level=1.1),
            ],
            PotentialBreach(id=1, channel_id=4, the_geom=LINE, exchange_level=1.1),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(
                    id=1,
                    the_geom=GEOM2,
                    calculation_pnt_id=1,
                    exchange_level=1.1,
                    levee_id=4,
                ),
                Levee(id=4, crest_level=1.2, max_breach_depth=0.5, material=1),
            ],
            PotentialBreach(
                id=1,
                channel_id=4,
                the_geom=LINE,
                exchange_level=1.1,
                maximum_breach_depth=0.5,
                levee_material=1,
            ),
        ],
    ],
)
def test_transform(session, objs, expected):
    session.add_all(objs)
    session.flush()
    actual = migration_213.transform(session, 1)

    assert_sqlalchemy_objects_equal(actual, expected)
