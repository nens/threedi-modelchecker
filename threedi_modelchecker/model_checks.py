from .checks.base import BaseCheck
from .checks.base import CheckLevel
from .checks.raster import LocalContext
from .checks.raster import ServerContext
from .config import Config
from .schema import ModelSchema
from .threedi_database import ThreediDatabase
from typing import Dict
from typing import Iterator
from typing import NamedTuple
from typing import Optional
from typing import Tuple


__all__ = ["ThreediModelChecker"]


class ThreediModelChecker:
    def __init__(self, threedi_db: ThreediDatabase, context: Optional[Dict] = None):
        """Initialize the model checker.

        Optionally, supply the context of the model check:
        - "available_rasters": a set of raster options that are available
        """
        self.db = threedi_db
        self.schema = ModelSchema(self.db)
        self.schema.validate_schema()
        self.config = Config(self.models)
        if context is None:
            self.context = LocalContext(base_path=self.db.base_path)
        else:
            self.context = ServerContext(**context)

    @property
    def models(self):
        """Returns a list of declared models"""
        return self.schema.declared_models

    def errors(self, level=CheckLevel.ERROR) -> Iterator[Tuple[BaseCheck, NamedTuple]]:
        """Iterates and applies checks, returning any failing rows.

        By default, checks of WARNING and INFO level are ignored.

        :return: Tuple of the applied check and the failing row.
        """
        session = self.db.get_session()
        session.model_checker_context = self.context
        for check in self.checks(level=level):
            model_errors = check.get_invalid(session)
            for error_row in model_errors:
                yield check, error_row

    def checks(self, level=CheckLevel.ERROR) -> Iterator[BaseCheck]:
        """Iterates over all configured checks

        :return: implementations of BaseChecks
        """
        for check in self.config.iter_checks(level=level):
            yield check

    def check_table(self, table):
        pass

    def check_column(self, column):
        pass
