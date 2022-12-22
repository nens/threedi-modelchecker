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
ConnectionNode = migration_213.ConnectionNode
Manhole = migration_213.Manhole
Channel = migration_213.Channel


@pytest.fixture
def sqlite_v212():
    """An in-memory database with schema version 212"""
    db = ThreediDatabase("")
    ModelSchema(db).upgrade("0212", backup=False, set_views=False)
    return db


@pytest.fixture
def session(sqlite_v212):
    return sqlite_v212.get_session()


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
        [
            CalculationPoint(id=1, the_geom=GEOM1),
            ConnectedPoint(
                id=1, the_geom=GEOM2, calculation_pnt_id=1, exchange_level=1.0
            ),
        ],
        [
            CalculationPoint(id=1, the_geom=GEOM1),
            ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1, levee_id=1),
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
    if a is None:
        return
    assert todict(a) == todict(b)


@pytest.mark.parametrize(
    "objs,expected",
    [
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
            ],
            PotentialBreach(channel_id=4, the_geom=LINE, code="1#123#4#v2_channel#4"),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(
                    id=1, the_geom=GEOM2, calculation_pnt_id=1, exchange_level=1.1
                ),
            ],
            PotentialBreach(
                channel_id=4,
                the_geom=LINE,
                exchange_level=1.1,
                code="1#123#4#v2_channel#4",
            ),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#4#v2_channel#4"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1, levee_id=4),
                Levee(id=4, crest_level=1.1),
            ],
            PotentialBreach(
                channel_id=4,
                the_geom=LINE,
                exchange_level=1.1,
                code="1#123#4#v2_channel#4",
            ),
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
                Levee(
                    id=4,
                    crest_level=1.2,
                    max_breach_depth=0.5,
                    material=1,
                ),
            ],
            PotentialBreach(
                channel_id=4,
                the_geom=LINE,
                exchange_level=1.1,
                maximum_breach_depth=0.5,
                levee_material=1,
                code="1#123#4#v2_channel#4",
            ),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#3#v2_manhole#1"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
                Manhole(id=3, connection_node_id=6),
                ConnectionNode(id=6),
                Channel(id=4, connection_node_start_id=6, calculation_type=102),
            ],
            PotentialBreach(channel_id=4, the_geom=LINE, code="1#123#3#v2_manhole#1"),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#3#v2_manhole#1"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
                Manhole(id=3, connection_node_id=6),
                ConnectionNode(id=6),
                Channel(id=4, connection_node_end_id=6, calculation_type=102),
            ],
            PotentialBreach(channel_id=4, the_geom=LINE, code="1#123#3#v2_manhole#1"),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#3#v2_manhole#1"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
                Manhole(id=3, connection_node_id=6),
                ConnectionNode(id=6),
                Channel(id=4, connection_node_start_id=6, calculation_type=105),
            ],
            PotentialBreach(channel_id=4, the_geom=LINE, code="1#123#3#v2_manhole#1"),
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#3#v2_manhole#1"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
                Manhole(id=3, connection_node_id=6),
                ConnectionNode(id=6),
            ],
            None,
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#3#v2_manhole#1"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
                Manhole(id=3, connection_node_id=6),
                ConnectionNode(id=6),
                Channel(id=4, connection_node_start_id=6, calculation_type=101),
            ],
            None,
        ],
        [
            [
                CalculationPoint(id=1, the_geom=GEOM1, user_ref="123#3#v2_manhole#1"),
                ConnectedPoint(id=1, the_geom=GEOM2, calculation_pnt_id=1),
                Manhole(id=3, connection_node_id=6),
                ConnectionNode(id=6),
                Channel(id=3, connection_node_start_id=6, calculation_type=102),
                Channel(id=5, connection_node_start_id=6, calculation_type=105),
                Channel(id=4, connection_node_end_id=6, calculation_type=105),
            ],
            PotentialBreach(channel_id=4, the_geom=LINE, code="1#123#3#v2_manhole#1"),
        ],
    ],
)
def test_to_potential_breach(session, objs, expected):
    session.add_all(objs)
    session.flush()
    actual = migration_213.to_potential_breach(session, 1)

    assert_sqlalchemy_objects_equal(actual, expected)
