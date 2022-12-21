from importlib.machinery import SourceFileLoader
from pathlib import Path
from threedi_modelchecker import ThreediDatabase
from threedi_modelchecker.schema import ModelSchema
from threedi_modelchecker.threedi_model.models import CalculationPoint
from threedi_modelchecker.threedi_model.models import ConnectedPoint

import pytest
import threedi_modelchecker


@pytest.fixture
def in_memory_sqlite():
    """An in-memory database with the most recent schema"""
    db = ThreediDatabase("")
    ModelSchema(db).upgrade("0212", backup=False, set_views=False)
    return db


@pytest.fixture
def connection(in_memory_sqlite):
    with in_memory_sqlite.get_engine().connect() as connection:
        yield connection


@pytest.fixture
def migration_213():
    path = (
        Path(threedi_modelchecker.__file__).parent
        / "migrations"
        / "versions"
        / "0213_connected_points_to_breaches.py"
    )
    return SourceFileLoader("migration_213", str(path)).load_module("migration_213")


GEOM1 = "SRID=4326;POINT (0 0)"
GEOM2 = "SRID=4326;POINT (0 1)"


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
def test_clean_connected_points(in_memory_sqlite, connection, migration_213, objs):
    session = in_memory_sqlite.get_session()
    session.add_all(objs)
    session.flush()
    migration_213.clean_connected_points(connection)
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
def test_clean_connected_points_keep(in_memory_sqlite, connection, migration_213, objs):
    session = in_memory_sqlite.get_session()
    session.add_all(objs)
    session.flush()
    migration_213.clean_connected_points(connection)

    actual = (
        session.query(CalculationPoint).count() + session.query(ConnectedPoint).count()
    )
    assert actual == len(objs)
