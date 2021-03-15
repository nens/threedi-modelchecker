from .errors import MigrationMissingError
from .errors import MigrationTooHighError
from .threedi_model import constants
from .threedi_model import models
from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from contextlib import contextmanager
from sqlalchemy import Column
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Table


def get_alembic_config(connection=None):
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "threedi_modelchecker:migrations")
    if connection is not None:
        alembic_cfg.attributes["connection"] = connection
    return alembic_cfg


def get_schema_version():
    """Returns the version of the schema in this library"""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    with EnvironmentContext(config=config, script=script) as env:
        return int(env.get_head_revision())


class ModelSchema:
    def __init__(self, threedi_db, declared_models=models.DECLARED_MODELS):
        self.db = threedi_db
        self.declared_models = declared_models

    def _get_version_old(self):
        """The version of the database using the old 'south' versioning.
        """
        south_migrationhistory = Table(
            "south_migrationhistory", MetaData(), Column("id", Integer)
        )
        engine = self.db.get_engine()
        if not engine.has_table("south_migrationhistory"):
            return
        with engine.connect() as connection:
            query = south_migrationhistory.select().order_by(
                south_migrationhistory.columns["id"].desc()
            )
            versions = list(connection.execute(query.limit(1)))
            if len(versions) == 1:
                return versions[0][0]
            else:
                return None

    def get_version(self):
        """Returns the id (integer) of the latest migration"""
        with self.db.get_engine().connect() as connection:
            context = MigrationContext.configure(connection)
            version = context.get_current_revision()

        if version is not None:
            return int(version)
        else:
            return self._get_version_old()

    def upgrade(self):
        """Upgrade the sqlite inplace"""
        if self.get_version() < constants.LATEST_SOUTH_MIGRATION_ID:
            raise MigrationMissingError

        with self.db.get_engine().begin() as connection:
            command.upgrade(get_alembic_config(connection), "head")

    def validate_schema(self):
        """Very basic validation of 3Di schema.

        Check that the database has the latest migration applied. If the
        latest migrations is applied, we assume the database also contains all
        tables and columns defined in threedi_model.models.py.

        :return: True if the threedi_db schema is valid, raises an error otherwise.
        :raise MigrationMissingError, MigrationTooHighError
        """
        migration_id = self.get_version()
        if migration_id is None or migration_id < constants.MIN_SCHEMA_VERSION:
            raise MigrationMissingError
        elif migration_id > get_schema_version():
            raise MigrationTooHighError
        return True

    def get_missing_tables(self):
        pass

    def get_missing_columns(self):
        pass
