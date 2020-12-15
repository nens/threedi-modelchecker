from sqlalchemy import func

from .threedi_model import constants
from .threedi_model import models
from .errors import MigrationMissingError
from .errors import MigrationTooHighError  # noqa
from .errors import MigrationNameError  # noqa
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from threedi_modelchecker.threedi_database import ThreediDatabase
from typing import List
from typing import Optional
from typing import Tuple


class ModelSchema:
    def __init__(self, threedi_db: ThreediDatabase, declared_models: List[DeclarativeMeta] = models.DECLARED_MODELS) -> None:
        self.db = threedi_db
        self.declared_models = declared_models

    def _latest_migration(self) -> Tuple[Optional[int], Optional[str]]:
        """Returns a tuple with latest migration id and name"""
        session = self.db.get_session()
        latest_migration_id = session.query(
            func.max(models.SouthMigrationHistory.id)
        ).scalar()
        latest_migration_name = (
            session.query(models.SouthMigrationHistory.migration)
            .filter(models.SouthMigrationHistory.id == latest_migration_id)
            .scalar()
        )
        return latest_migration_id, latest_migration_name

    def validate_schema(self) -> bool:
        """Very basic validation of 3Di schema.

        Check that the database has the latest migration applied. If the
        latest migrations is applied, we assume the database also contains all
        tables and columns defined in threedi_model.models.py.

        :return: True if the threedi_db schema is valid, raises an error otherwise.
        :raise MigrationMissingError, MigrationTooHighError, MigrationNameError
        """
        migration_id, migration_name = self._latest_migration()
        if migration_id is None or migration_id < constants.LATEST_MIGRATION_ID:
            raise MigrationMissingError
        # TODO: on 08-07-2019 3Di has been released with the newest migration
        #  174: '0172_auto__del_v2initialwaterlevel__del_field_v2orifice_max_capacity__del_f'.  # noqa
        #  This migrations deletes some fields, which were already not present in the
        #  models of the threedi-modelchecker. Therefore we can both accept migration
        #  173 and 174.
        #  Because inpy has not been run over all the existing models during this new
        #  release, models downloaded via 3id.lizard.net/models still have the
        #  migration 173 (unless a user has specifically re-run inpy for the model).
        elif migration_id > constants.LATEST_MIGRATION_ID:
            # don't raise warning for now, see comments above.
            # raise MigrationTooHighError
            pass
        elif migration_name != constants.LATEST_MIGRATION_NAME:
            # don't fix on a specific migration name, see comments above.
            # raise MigrationNameError
            pass
        return (
            migration_id == constants.LATEST_MIGRATION_ID
            and migration_name == constants.LATEST_MIGRATION_NAME
        )

    def get_missing_tables(self):
        pass

    def get_missing_columns(self):
        pass
