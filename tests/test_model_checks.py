from pathlib import Path
from threedi_modelchecker.config import CHECKS
from threedi_modelchecker.model_checks import BaseCheck
from threedi_modelchecker.model_checks import LocalContext
from threedi_modelchecker.model_checks import ThreediModelChecker
from unittest import mock

import pytest


@pytest.fixture
def model_checker(threedi_db):
    with mock.patch("threedi_modelchecker.model_checks.ModelSchema"):
        return ThreediModelChecker(threedi_db)


def test_set_base_path(model_checker):
    assert model_checker.context.base_path == Path(model_checker.db.path).parent


@pytest.mark.filterwarnings("error::")
def test_get_model_error_iterator(model_checker):
    errors = list(model_checker.errors(level="info"))
    assert len(errors) == 0


def id_func(param):
    if isinstance(param, BaseCheck):
        return "check {}-".format(param.error_code)
    return repr(param)


@pytest.mark.filterwarnings("error::")
@pytest.mark.parametrize("check", CHECKS, ids=id_func)
def test_individual_checks(threedi_db, check):
    session = threedi_db.get_session()
    session.model_checker_context = LocalContext(base_path=threedi_db.base_path)
    assert len(check.get_invalid(session)) == 0
