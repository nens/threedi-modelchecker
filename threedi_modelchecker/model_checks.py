from .schema import ModelSchema
from .threedi_model import models, custom_types
from .config import Config


class ThreediModelChecker:

    def __init__(self, threedi_db):
        self.db = threedi_db
        self.schema = ModelSchema(self.db)
        self.config = Config(self.models)

    @property
    def models(self):
        return self.schema.declared_models

    def get_model_errors(self):
        model_errors = []
        session = self.db.get_session()
        for check in self.config.checks:
            model_errors += check.get_invalid(session)
        return model_errors

    def get_model_error_iterator(self):
        session = self.db.get_session()
        for check in self.config.checks:
            model_errors = check.get_invalid(session)
            if model_errors:
                for error in model_errors:
                    yield error

    def check_table(self, table):
        pass

    def check_column(self, column):
        pass

    def apply(self, check):
        """Applies the check and returns any invalid rows"""
        pass
