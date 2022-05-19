from .errors import MigrationMissingError
from .threedi_model import constants
from .threedi_model import models
from .threedi_model import views
from alembic.config import Config
from alembic import command as alembic_command
from alembic.environment import EnvironmentContext
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import Table
from sqlalchemy import inspect
from .spatialite_versions import get_spatialite_version, copy_models
import warnings


__all__ = ["ModelSchema"]


def get_alembic_config(connection=None):
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "threedi_modelchecker:migrations")
    alembic_cfg.set_main_option("version_table", constants.VERSION_TABLE_NAME)
    if connection is not None:
        alembic_cfg.attributes["connection"] = connection
    return alembic_cfg


def get_schema_version():
    """Returns the version of the schema in this library"""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    with EnvironmentContext(config=config, script=script) as env:
        return int(env.get_head_revision())


def _is_empty_database(db):
    """Check if there are tables in the database"""
    engine = db.get_engine()
    inspector = inspect(engine)
    return len(inspector.get_table_names()) == 0


def _create_database(db):
    """Create the 3Di model schema in an empty ThreediDatabase instance"""
    engine = db.get_engine()

    if engine.dialect.name == "sqlite":
        with db.session_scope() as session:
            # Speed up by journalling in memory; in case of a crash the database
            # will likely go corrupt, however we have an empty database here so
            # that is no problem.
            session.execute("PRAGMA journal_mode = MEMORY")
            session.execute("SELECT InitSpatialMetadata()")

    models.Base.metadata.create_all(engine)

    with engine.begin() as connection:
        config = get_alembic_config(connection)
        alembic_command.stamp(config, "head")


def _upgrade_database(db, revision="head"):
    """Upgrade ThreediDatabase instance"""
    engine = db.get_engine()

    # Fast track the upgrade to the latest version if database is empty
    if revision in {"head", get_schema_version()} and _is_empty_database(db):
        return _create_database(db)

    with engine.begin() as connection:
        config = get_alembic_config(connection)
        alembic_command.upgrade(config, revision)


class ModelSchema:
    def __init__(self, threedi_db, declared_models=models.DECLARED_MODELS):
        self.db = threedi_db
        self.declared_models = declared_models

    def _get_version_old(self):
        """The version of the database using the old 'south' versioning."""
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
            context = MigrationContext.configure(
                connection, opts={"version_table": constants.VERSION_TABLE_NAME}
            )
            version = context.get_current_revision()

        if version is not None:
            return int(version)
        else:
            return self._get_version_old()

    def upgrade(
        self,
        revision="head",
        backup=True,
        set_views=True,
        upgrade_spatialite_version=False,
    ):
        """Upgrade the database to the latest version.

        This requires either a completely empty database or a database with its
        current schema version at least 174 (the latest migration of the old
        model databank).

        The upgrade is done using database transactions. However, for SQLite,
        database transactions are only partially supported. To ensure that the
        database file does not become corrupt, enable the "backup" parameter.
        If the database is temporary already (or if it is PostGIS), disable
        it.

        Specify 'set_views=True' to also (re)create views after the upgrade.
        This is not compatible when upgrading to a different version than the
        latest version.

        Specify 'upgrade_spatialite_version=True' to also upgrade the
        spatialite file version after the upgrade.
        """
        if upgrade_spatialite_version and not set_views:
            raise ValueError(
                "Cannot upgrade the spatialite version without setting the views."
            )
        v = self.get_version()
        if v is not None and v < constants.LATEST_SOUTH_MIGRATION_ID:
            raise MigrationMissingError(
                f"The modelchecker cannot update versions below "
                f"{constants.LATEST_SOUTH_MIGRATION_ID}. Please consult the "
                f"3Di documentation on how to update legacy databases."
            )
        if set_views and revision not in ("head", get_schema_version()):
            raise ValueError(f"Cannot set views when upgrading to version '{revision}'")
        if backup:
            with self.db.file_transaction() as work_db:
                _upgrade_database(work_db, revision=revision)
        else:
            _upgrade_database(self.db, revision=revision)

        if upgrade_spatialite_version:
            self.upgrade_spatialite_version()
        elif set_views:
            self.set_views()

    def validate_schema(self):
        """Very basic validation of 3Di schema.

        Check that the database has the latest migration applied. If the
        latest migrations is applied, we assume the database also contains all
        tables and columns defined in threedi_model.models.py.

        :return: True if the threedi_db schema is valid, raises an error otherwise.
        :raise MigrationMissingError, MigrationTooHighError
        """
        version = self.get_version()
        schema_version = get_schema_version()
        if version is None or version < schema_version:
            raise MigrationMissingError(
                f"The modelchecker requires at least schema version "
                f"{schema_version}. Current version: {version}."
            )

        if version > schema_version:
            warnings.warn(
                f"The database version is higher than the modelchecker "
                f"({version} > {schema_version}). This may lead to unexpected "
                f"results. "
            )
        return True

    def get_missing_tables(self):
        pass

    def get_missing_columns(self):
        pass

    def set_views(self):
        """(Re)create views in the spatialite according to the latest definitions."""
        version = self.get_version()
        schema_version = get_schema_version()
        _, file_version = get_spatialite_version(self.db)

        if version != get_schema_version():
            raise MigrationMissingError(
                f"Setting views requires schema version "
                f"{schema_version}. Current version: {version}."
            )

        with self.db.get_engine().begin() as connection:
            for (name, view) in views.ALL_VIEWS.items():
                connection.execute(f"DROP VIEW IF EXISTS {name}")
                connection.execute(
                    f"DELETE FROM views_geometry_columns WHERE view_name = '{name}'"
                )
                connection.execute(f"CREATE VIEW {name} AS {view['definition']}")
                if file_version == 3:
                    connection.execute(
                        f"INSERT INTO views_geometry_columns (view_name, view_geometry,view_rowid,f_table_name,f_geometry_column) VALUES('{name}', '{view['view_geometry']}', '{view['view_rowid']}', '{view['f_table_name']}', '{view['f_geometry_column']}')"
                    )
                else:
                    connection.execute(
                        f"INSERT INTO views_geometry_columns (view_name, view_geometry,view_rowid,f_table_name,f_geometry_column,read_only) VALUES('{name}', '{view['view_geometry']}', '{view['view_rowid']}', '{view['f_table_name']}', '{view['f_geometry_column']}', 0)"
                    )
            for name in views.VIEWS_TO_DELETE:
                connection.execute(f"DROP VIEW IF EXISTS {name}")
                connection.execute(
                    f"DELETE FROM views_geometry_columns WHERE view_name = '{name}'"
                )

    def upgrade_spatialite_version(self):
        """Upgrade the version of the spatialite file to the version of the
        current spatialite library.

        Does nothing if the current file version > 3 or if the current library
        version is not 4 or 5.

        Raises UpgradeFailedError if there are any SQL constraints violated.
        """
        lib_version, file_version = get_spatialite_version(self.db)
        if file_version == 3 and lib_version in (4, 5):
            self.validate_schema()

            with self.db.file_transaction(start_empty=True) as work_db:
                work_schema = ModelSchema(work_db)
                work_schema.upgrade(
                    backup=False, set_views=True, upgrade_spatialite_version=False
                )
                copy_models(self.db, work_db, self.declared_models)
