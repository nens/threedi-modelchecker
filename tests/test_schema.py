import pytest

from . import factories
from threedi_modelchecker.schema import ModelSchema, constants
from threedi_modelchecker import errors


def test_get_migration_info(threedi_db):
    factories.MigrationHistoryFactory(
        id=constants.LATEST_MIGRATION_ID,
        migration=constants.LATEST_MIGRATION_NAME
    )
    schema_checker = ModelSchema(threedi_db)
    migration_id, migration_name = schema_checker._latest_migration()
    assert migration_id == constants.LATEST_MIGRATION_ID
    assert migration_name == constants.LATEST_MIGRATION_NAME


def test_validate_schema(threedi_db):
    factories.MigrationHistoryFactory(
        id=constants.LATEST_MIGRATION_ID,
        migration=constants.LATEST_MIGRATION_NAME
    )
    schema = ModelSchema(threedi_db)
    assert schema.validate_schema()


def test_validate_schema_missing_migration(threedi_db):
    factories.MigrationHistoryFactory(
        id=-1
    )
    schema = ModelSchema(threedi_db)
    with pytest.raises(errors.MigrationMissingError):
        schema.validate_schema()


def test_validate_schema_no_migrations(threedi_db):
    schema = ModelSchema(threedi_db)
    migration_id, migration_name = schema._latest_migration()
    assert migration_id is None
    with pytest.raises(errors.MigrationMissingError):
        schema.validate_schema()
