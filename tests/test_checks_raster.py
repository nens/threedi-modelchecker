from tests import factories
from threedi_modelchecker.checks.raster import BaseRasterCheck
from threedi_modelchecker.checks.raster import LocalContext
from threedi_modelchecker.checks.raster import RasterExistsCheck
from threedi_modelchecker.checks.raster import ServerContext
from threedi_modelchecker.threedi_model import models
from unittest import mock

import pytest


@pytest.fixture
def mocked_check():
    with mock.patch.object(BaseRasterCheck, "is_valid_local", return_value=True):
        with mock.patch.object(BaseRasterCheck, "is_valid_server", return_value=True):
            yield BaseRasterCheck(column=models.GlobalSetting.dem_file)


@pytest.fixture
def context_local(tmp_path):
    return LocalContext(base_path=tmp_path)


@pytest.fixture
def context_server():
    return ServerContext(available_rasters={})


@pytest.fixture
def session_local(session, context_local):
    session.model_checker_context = context_local
    return session


@pytest.fixture
def session_server(session, context_server):
    session.model_checker_context = context_server
    return session


def test_base_to_check(session):
    factories.GlobalSettingsFactory(dem_file="somefile")
    check = BaseRasterCheck(column=models.GlobalSetting.dem_file)
    assert check.to_check(session).count() == 1


def test_base_to_check_ignores_empty(session):
    factories.GlobalSettingsFactory(dem_file="")
    check = BaseRasterCheck(column=models.GlobalSetting.dem_file)
    assert check.to_check(session).count() == 0


def test_base_to_check_ignores_none(session):
    factories.GlobalSettingsFactory(dem_file=None)
    check = BaseRasterCheck(column=models.GlobalSetting.dem_file)
    assert check.to_check(session).count() == 0


def test_base_get_invalid_local(mocked_check, session_local):
    factories.GlobalSettingsFactory(dem_file="somefile")
    assert mocked_check.get_invalid(session_local) == []
    mocked_check.is_valid_local.assert_called_once_with(
        "somefile", session_local.model_checker_context
    )
    assert not mocked_check.is_valid_server.called


def test_base_get_invalid_server(mocked_check, session_server):
    factories.GlobalSettingsFactory(dem_file="somefile")
    assert mocked_check.get_invalid(session_server) == []
    mocked_check.is_valid_server.assert_called_once_with(
        "somefile", session_server.model_checker_context
    )
    assert not mocked_check.is_valid_local.called


@pytest.fixture
def exists_check():
    return RasterExistsCheck(column=models.GlobalSetting.dem_file)


def test_exists_is_valid_local_ok(context_local, tmp_path, exists_check):
    (tmp_path / "somefile").touch()
    assert exists_check.is_valid_local("somefile", context_local)


def test_exists_is_valid_local_err(context_local, exists_check):
    assert not exists_check.is_valid_local("somefile", context_local)


def test_exists_is_valid_server_ok(context_server, exists_check):
    context_server.available_rasters = {"dem_file"}
    assert exists_check.is_valid_server("somefile", context_server)


def test_exists_is_valid_server_err(context_server, exists_check):
    context_server.available_rasters = {"other"}
    assert not exists_check.is_valid_server("somefile", context_server)
