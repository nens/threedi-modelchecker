import pytest

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.exporters import format_check_results
from tests.factories import MigrationHistoryFactory
from threedi_modelchecker.threedi_model import constants


@pytest.fixture
def model_checker(threedi_db):
    MigrationHistoryFactory(
        id=constants.LATEST_MIGRATION_ID,
        migration=constants.LATEST_MIGRATION_NAME,
    )
    return ThreediModelChecker(threedi_db)


def test_get_model_error_iterator(model_checker):
    for check, error in model_checker.errors():
        print(format_check_results(check, error))
