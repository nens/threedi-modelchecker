import pytest

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.exporters import format_check_results
from threedi_modelchecker.threedi_model import constants

from unittest import mock

@pytest.fixture
def model_checker(threedi_db):
    with mock.patch("threedi_modelchecker.model_checks.ModelSchema"):
        return ThreediModelChecker(threedi_db)


def test_get_model_error_iterator(model_checker):
    for check, error in model_checker.errors():
        print(format_check_results(check, error))
