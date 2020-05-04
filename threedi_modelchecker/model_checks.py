from .checks.base import BaseCheck
from .threedi_database import ThreediDatabase
from .schema import ModelSchema
from .config import Config

from typing import Iterator, Tuple, NamedTuple


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

    def errors(
            self, table: str = None, column: str = None
    ) -> Iterator[Tuple[BaseCheck, NamedTuple]]:
        """Iterates and applies checks, returning any failing rows.

        :param table: optional; only checks on `table` will be applied
        :param column: optional; requires `table` to also be present. Only checks on
            `table` and `column` will be applied.
        :return: Tuple of the applied check and the failing row.
        """
        session = self.db.get_session()
        to_check = self.checks(table, column)
        for check in to_check:
            model_errors = check.get_invalid(session)
            for error_row in model_errors:
                yield check, error_row

    def checks(self, table: str = None, column: str = None) -> Iterator[BaseCheck]:
        """Iterates over all configured checks

        :return: implementations of BaseChecks
        """
        checks = self.config.checks
        if table is not None:
            checks = getattr(self.config.checks, table)
            if column is not None:
                checks = getattr(checks, column)
        for check in checks:
            yield check
