from .checks.base import BaseCheck
from .config import Config
from .schema import ModelSchema
from .threedi_database import ThreediDatabase
from typing import Iterator
from typing import NamedTuple
from typing import Tuple


__all__ = ["ThreediModelChecker"]


class ThreediModelChecker:
    def __init__(self, threedi_db: ThreediDatabase):
        self.db = threedi_db
        self.schema = ModelSchema(self.db)
        self.schema.validate_schema()
        self.config = Config(self.models)

    @property
    def models(self):
        """Returns a list of declared models"""
        return self.schema.declared_models

    def errors(self) -> Iterator[Tuple[BaseCheck, NamedTuple]]:
        """Iterates and applies checks, returning any failing rows.

        :return: Tuple of the applied check and the failing row.
        """
        session = self.db.get_session()
        for check in self.checks():
            model_errors = check.get_invalid(session)
            for error_row in model_errors:
                yield check, error_row

    def checks(self) -> Iterator[BaseCheck]:
        """Iterates over all configured checks

        :return: implementations of BaseChecks
        """
        for check in self.config.checks:
            yield check

    def check_table(self, table):
        pass

    def check_column(self, column):
        pass
