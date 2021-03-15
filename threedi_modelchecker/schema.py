from .errors import MigrationMissingError
from .errors import MigrationTooHighError  # noqa
from .threedi_model import constants
from .threedi_model import models
from sqlalchemy import func

from contextlib import contextmanager

from alembic.migration import MigrationContext


class ModelSchema:
    def __init__(self, threedi_db, declared_models=models.DECLARED_MODELS):
        self.db = threedi_db
        self.declared_models = declared_models

    @contextmanager
    def migration_context(self):
        with self.db.get_engine().connect() as connection:
            yield MigrationContext.configure(connection)

    def _latest_migration_old(self):
        """Returns the id of the latest old ('south') migration"""
        with self.db.session_scope() as session:
            latest_migration_id = session.query(
                func.max(models.SouthMigrationHistory.id)
            ).scalar()
        return latest_migration_id

    def get_version(self):
        """Returns the id (integer) of the latest migration"""
        with self.migration_context() as context:
            version = context.get_current_revision()
    
        if version is not None:
            return int(version)
        else:
            return self._latest_migration_old()

    def validate_schema(self):
        """Very basic validation of 3Di schema.

        Check that the database has the latest migration applied. If the
        latest migrations is applied, we assume the database also contains all
        tables and columns defined in threedi_model.models.py.

        :return: True if the threedi_db schema is valid, raises an error otherwise.
        :raise MigrationMissingError, MigrationTooHighError
        """
        migration_id = self._latest_migration()
        if migration_id is None or migration_id < constants.LATEST_MIGRATION_ID:
            raise MigrationMissingError
        elif migration_id > constants.LATEST_MIGRATION_ID:
            # don't raise warning for now, see comments above.
            # raise MigrationTooHighError
            pass
        return migration_id == constants.LATEST_MIGRATION_ID

    def get_missing_tables(self):
        pass

    def get_missing_columns(self):
        pass
