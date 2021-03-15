from .errors import MigrationMissingError
from .errors import MigrationTooHighError
from .threedi_model import constants
from .threedi_model import models
from sqlalchemy import func

from contextlib import contextmanager

from alembic.migration import MigrationContext
from alembic import command
from alembic.config import Config


class ModelSchema:
    def __init__(self, threedi_db, declared_models=models.DECLARED_MODELS):
        self.db = threedi_db
        self.declared_models = declared_models

    def _latest_migration_old(self):
        """Returns the id of the latest old ('south') migration"""
        with self.db.session_scope() as session:
            latest_migration_id = session.query(
                func.max(models.SouthMigrationHistory.id)
            ).scalar()
        return latest_migration_id

    def get_version(self):
        """Returns the id (integer) of the latest migration"""
        with self.db.get_engine().connect() as connection:
            context = MigrationContext.configure(connection)
            version = context.get_current_revision()
    
        if version is not None:
            return int(version)
        else:
            return self._latest_migration_old()

    def upgrade(self):
        """Upgrade the sqlite inplace"""
        if self.get_version() < constants.LATEST_SOUTH_MIGRATION_ID:
            raise MigrationMissingError

        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "threedi_modelchecker:migrations")

        with self.db.get_engine().begin() as connection:
            alembic_cfg.attributes["connection"] = connection
            command.upgrade(alembic_cfg, "head")

    def validate_schema(self):
        """Very basic validation of 3Di schema.

        Check that the database has the latest migration applied. If the
        latest migrations is applied, we assume the database also contains all
        tables and columns defined in threedi_model.models.py.

        :return: True if the threedi_db schema is valid, raises an error otherwise.
        :raise MigrationMissingError, MigrationTooHighError
        """
        migration_id = self._latest_migration()
        if migration_id is None or migration_id < constants.MIMIMUM_MIGRATION_ID:
            raise MigrationMissingError
        elif migration_id > constants.LATEST_MIGRATION_ID:
            raise MigrationTooHighError
        return True

    def get_missing_tables(self):
        pass

    def get_missing_columns(self):
        pass
