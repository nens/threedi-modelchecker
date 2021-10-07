from .conftest import emtpy_sqlite_path
from pathlib import Path
from threedi_modelchecker.model_checks import ThreediModelChecker
from unittest import mock

import pytest


@pytest.fixture
def model_checker(threedi_db):
    with mock.patch("threedi_modelchecker.model_checks.ModelSchema"):
        return ThreediModelChecker(threedi_db)


def test_set_base_path(model_checker):
    if model_checker.db.db_type == "postgres":
        pytest.skip("postgres does not have a base_path in its context")
    assert model_checker.context.base_path == Path(emtpy_sqlite_path).parent


@pytest.mark.filterwarnings("error::")
def test_get_model_error_iterator(model_checker):
    errors = list(model_checker.errors(level="info"))
    assert len(errors) == 0
