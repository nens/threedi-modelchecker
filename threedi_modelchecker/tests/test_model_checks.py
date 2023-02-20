from unittest import mock

import pytest
from threedi_schema import ThreediDatabase

from threedi_modelchecker.config import CHECKS
from threedi_modelchecker.model_checks import (
    BaseCheck,
    LocalContext,
    ThreediModelChecker,
)


@pytest.fixture
def model_checker(threedi_db):
    with mock.patch.object(ThreediDatabase, "schema"):
        return ThreediModelChecker(threedi_db)


@pytest.mark.parametrize(
    "context",
    [
        {},
        None,
        {"context_type": "local"},
        {"base_path": "<db>"},
        {"context_type": "local", "base_path": "<db>"},
    ],
)
def test_context_local(threedi_db, context):
    if context is not None and context.get("base_path") == "<db>":
        context["base_path"] = threedi_db.base_path
    with mock.patch.object(ThreediDatabase, "schema"):
        model_checker = ThreediModelChecker(threedi_db, context)
    assert model_checker.context.base_path == threedi_db.base_path


@pytest.mark.parametrize(
    "context",
    [
        {"context_type": "server", "available_rasters": {"foo": "bar"}},
    ],
)
def test_context_server(threedi_db, context):
    with mock.patch.object(ThreediDatabase, "schema"):
        model_checker = ThreediModelChecker(threedi_db, context)
    assert model_checker.context.available_rasters == {"foo": "bar"}


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
    with threedi_db.get_session() as session:
        session.model_checker_context = LocalContext(base_path=threedi_db.base_path)
        assert len(check.get_invalid(session)) == 0
