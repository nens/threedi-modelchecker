import pytest

from . import factories
from threedi_modelchecker.schema import ModelSchema, constants, get_schema_version
from threedi_modelchecker import errors
from sqlalchemy import MetaData, Column, Table, Integer, String

from unittest import mock


@pytest.fixture
def south_migration_table(in_memory_sqlite):
    south_migrationhistory = Table(
        "south_migrationhistory",
        MetaData(),
        Column("id", Integer),
    )
    engine = in_memory_sqlite.get_engine()
    south_migrationhistory.create(engine)
    return south_migrationhistory


@pytest.fixture
def alembic_versions_table(in_memory_sqlite):
    alembic_versions = Table(
        "alembic_version",
        MetaData(),
        Column("version_num", String(32), nullable=False),
    )
    engine = in_memory_sqlite.get_engine()
    alembic_versions.create(engine)
    return alembic_versions


def test_get_version_no_tables(in_memory_sqlite):
    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id is None


def test_get_version_empty_south(in_memory_sqlite, south_migration_table):
    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id is None


def test_get_version_south(in_memory_sqlite, south_migration_table):
    with in_memory_sqlite.get_engine().connect() as connection:
        for v in (42, 43):
            connection.execute(south_migration_table.insert().values(id=v))

    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id == 43


def test_get_version_empty_alembic(in_memory_sqlite, alembic_versions_table):
    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id is None


def test_get_version_alembic(in_memory_sqlite, alembic_versions_table):
    with in_memory_sqlite.get_engine().connect() as connection:
        connection.execute(alembic_versions_table.insert().values(version_num="0201"))

    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id == 201


def test_validate_schema(threedi_db):
    schema = ModelSchema(threedi_db)
    with mock.patch.object(schema, "get_version", return_value=constants.MIN_SCHEMA_VERSION):
        assert schema.validate_schema()


@pytest.mark.parametrize("version", [-1, constants.MIN_SCHEMA_VERSION - 1, None])
def test_validate_schema_missing_migration(threedi_db, version):
    schema = ModelSchema(threedi_db)
    with mock.patch.object(schema, "get_version", return_value=version):
        with pytest.raises(errors.MigrationMissingError):
            schema.validate_schema()


@pytest.mark.parametrize("version", [9999])
def test_validate_schema_too_high_migration(threedi_db, version):
    schema = ModelSchema(threedi_db)
    with mock.patch.object(schema, "get_version", return_value=version):
        with pytest.raises(errors.MigrationTooHighError):
            schema.validate_schema()
