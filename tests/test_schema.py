from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table
from threedi_modelchecker import errors
from threedi_modelchecker.schema import constants
from threedi_modelchecker.schema import get_schema_version
from threedi_modelchecker.schema import ModelSchema
from threedi_modelchecker.threedi_model.views import ALL_VIEWS
from threedi_modelchecker.spatialite_versions import get_spatialite_version
from unittest import mock

import pytest


@pytest.fixture
def south_migration_table(in_memory_sqlite):
    south_migrationhistory = Table(
        "south_migrationhistory", MetaData(), Column("id", Integer)
    )
    engine = in_memory_sqlite.get_engine()
    south_migrationhistory.create(engine)
    return south_migrationhistory


@pytest.fixture
def alembic_version_table(in_memory_sqlite):
    alembic_version = Table(
        constants.VERSION_TABLE_NAME,
        MetaData(),
        Column("version_num", String(32), nullable=False),
    )
    engine = in_memory_sqlite.get_engine()
    alembic_version.create(engine)
    return alembic_version


def test_get_schema_version():
    """The current version in the library. We start counting at 200."""
    # this will catch future mistakes of setting non-integer revisions
    assert get_schema_version() >= 200


def test_get_version_no_tables(in_memory_sqlite):
    """Get the version of a sqlite with no version tables"""
    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id is None


def test_get_version_empty_south(in_memory_sqlite, south_migration_table):
    """Get the version of a sqlite with an empty South version table"""
    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id is None


def test_get_version_south(in_memory_sqlite, south_migration_table):
    """Get the version of a sqlite with a South version table"""
    with in_memory_sqlite.get_engine().connect() as connection:
        for v in (42, 43):
            connection.execute(south_migration_table.insert().values(id=v))

    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id == 43


def test_get_version_empty_alembic(in_memory_sqlite, alembic_version_table):
    """Get the version of a sqlite with an empty alembic version table"""
    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id is None


def test_get_version_alembic(in_memory_sqlite, alembic_version_table):
    """Get the version of a sqlite with an alembic version table"""
    with in_memory_sqlite.get_engine().connect() as connection:
        connection.execute(alembic_version_table.insert().values(version_num="0201"))

    schema_checker = ModelSchema(in_memory_sqlite)
    migration_id = schema_checker.get_version()
    assert migration_id == 201


def test_validate_schema(threedi_db):
    """Validate a correct schema version"""
    schema = ModelSchema(threedi_db)
    with mock.patch.object(
        schema, "get_version", return_value=get_schema_version()
    ):
        assert schema.validate_schema()


@pytest.mark.parametrize("version", [-1, 205, None])
def test_validate_schema_missing_migration(threedi_db, version):
    """Validate a too low schema version"""
    schema = ModelSchema(threedi_db)
    with mock.patch.object(schema, "get_version", return_value=version):
        with pytest.raises(errors.MigrationMissingError):
            schema.validate_schema()


@pytest.mark.parametrize("version", [9999])
def test_validate_schema_too_high_migration(threedi_db, version):
    """Validate a too high schema version"""
    schema = ModelSchema(threedi_db)
    with mock.patch.object(schema, "get_version", return_value=version):
        with pytest.warns(UserWarning):
            schema.validate_schema()


def test_full_upgrade_empty(in_memory_sqlite):
    """Upgrade an empty database to the latest version"""
    schema = ModelSchema(in_memory_sqlite)
    schema.upgrade(backup=False, set_views=False, upgrade_spatialite_version=False)
    assert schema.get_version() == get_schema_version()
    assert in_memory_sqlite.get_engine().has_table("v2_connection_nodes")


def test_full_upgrade_with_preexisting_version(south_latest_sqlite):
    """Upgrade an empty database to the latest version"""
    schema = ModelSchema(south_latest_sqlite)
    schema.upgrade(backup=False, set_views=False, upgrade_spatialite_version=False)
    assert schema.get_version() == get_schema_version()
    assert south_latest_sqlite.get_engine().has_table("v2_connection_nodes")


def test_full_upgrade_oldest(oldest_sqlite):
    """Upgrade a legacy database to the latest version"""
    schema = ModelSchema(oldest_sqlite)
    schema.upgrade(backup=False, set_views=False, upgrade_spatialite_version=False)
    assert schema.get_version() == get_schema_version()
    assert oldest_sqlite.get_engine().has_table("v2_connection_nodes")


def test_upgrade_south_not_latest_errors(in_memory_sqlite):
    """Upgrading a database that is not at the latest south migration will error"""
    schema = ModelSchema(in_memory_sqlite)
    with mock.patch.object(
        schema, "get_version", return_value=constants.LATEST_SOUTH_MIGRATION_ID - 1
    ):
        with pytest.raises(errors.MigrationMissingError):
            schema.upgrade(backup=False, set_views=False, upgrade_spatialite_version=False)


def test_upgrade_with_backup(threedi_db):
    """Upgrading with backup=True will proceed on a copy of the database"""
    if threedi_db.db_type != "spatialite":
        pytest.skip()
    schema = ModelSchema(threedi_db)
    with mock.patch(
        "threedi_modelchecker.schema._upgrade_database", side_effect=RuntimeError
    ) as upgrade, mock.patch.object(schema, "get_version", return_value=199):
        with pytest.raises(RuntimeError):
            schema.upgrade(backup=True, set_views=False, upgrade_spatialite_version=False)

    (db,), kwargs = upgrade.call_args
    assert db is not threedi_db


def test_upgrade_without_backup(threedi_db):
    """Upgrading with backup=True will proceed on the database itself"""
    schema = ModelSchema(threedi_db)
    with mock.patch(
        "threedi_modelchecker.schema._upgrade_database", side_effect=RuntimeError
    ) as upgrade, mock.patch.object(schema, "get_version", return_value=199):
        with pytest.raises(RuntimeError):
            schema.upgrade(backup=False, set_views=False, upgrade_spatialite_version=False)

    (db,), kwargs = upgrade.call_args
    assert db is threedi_db


def test_set_views(oldest_sqlite):
    """Make sure that the views are regenerated
    """
    schema = ModelSchema(oldest_sqlite)
    schema.upgrade(backup=False, set_views=True, upgrade_spatialite_version=False)
    assert schema.get_version() == get_schema_version()

    # Test all views
    with oldest_sqlite.session_scope() as session:
        for view_name in ALL_VIEWS:
            session.execute(f"SELECT * FROM {view_name} LIMIT 1").fetchall()

def test_upgrade_spatialite_3(oldest_sqlite):
    lib_version, file_version_before = get_spatialite_version(oldest_sqlite)
    if lib_version == file_version_before:
        pytest.skip("Nothing to test: spatialite library version equals file version")

    schema = ModelSchema(oldest_sqlite)
    schema.upgrade(backup=False, upgrade_spatialite_version=True)

    _, file_version_after = get_spatialite_version(oldest_sqlite)
    assert file_version_after == lib_version
