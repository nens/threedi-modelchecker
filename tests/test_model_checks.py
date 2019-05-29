import pytest

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.exporters import format_check_results


@pytest.fixture
def model_checker(threedi_db):
    return ThreediModelChecker(threedi_db)


def test_get_model_errors(model_checker):
    model_errors = model_checker.get_model_errors()


def test_get_model_error_iterator(model_checker):
    error_iterator = model_checker.get_model_error_iterator()
    for check, error in error_iterator:
        print(format_check_results(check, error))
