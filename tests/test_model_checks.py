import pytest

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.exporters import format_check_results


@pytest.fixture
def model_checker(threedi_db):
    return ThreediModelChecker(threedi_db)


def test_get_model_error_iterator(model_checker):
    for check, error in model_checker.errors():
        print(format_check_results(check, error))
