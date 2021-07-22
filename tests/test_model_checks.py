import pytest

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.exporters import format_check_results
from .conftest import emtpy_sqlite_path

from pathlib import Path
from unittest import mock
import pytest


@pytest.fixture
def model_checker(threedi_db):
    with mock.patch("threedi_modelchecker.model_checks.ModelSchema"):
        return ThreediModelChecker(threedi_db)


def test_set_base_path(model_checker):
    if model_checker.db.db_type == "postgis":
        pytest.skip("postgis does not have a base_path in the context")
    assert model_checker.context.base_path == Path(emtpy_sqlite_path).parent


def test_get_model_error_iterator(model_checker):
    for check, error in model_checker.errors():
        print(format_check_results(check, error))
