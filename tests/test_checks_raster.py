from tests import factories
from threedi_modelchecker.checks.raster import LocalContext
from threedi_modelchecker.checks.raster import RasterExistsCheck
from threedi_modelchecker.checks.raster import ServerContext
from threedi_modelchecker.threedi_model import models


def test_exists_check_filesystem_ok(session, tmp_path):
    (tmp_path / "somefile").touch()
    factories.GlobalSettingsFactory(dem_file="somefile")
    session.model_checker_context = LocalContext(base_path=tmp_path)
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_exists_check_filesystem_ignore(session, tmp_path):
    factories.GlobalSettingsFactory(dem_file="")
    session.model_checker_context = LocalContext(base_path=tmp_path)
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_exists_check_filesystem_err(session, tmp_path):
    factories.GlobalSettingsFactory(dem_file="some/file")
    session.model_checker_context = LocalContext(base_path=tmp_path)
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_exists_check_context_ok(session):
    factories.GlobalSettingsFactory(dem_file="some/file")
    session.model_checker_context = ServerContext(available_rasters={"dem_file"})
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_exists_check_context_err(session):
    factories.GlobalSettingsFactory(dem_file="some/file")
    session.model_checker_context = ServerContext(available_rasters={"frict_coef_file"})
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_exists_check_context_ignore(session):
    factories.GlobalSettingsFactory(dem_file="")
    session.model_checker_context = ServerContext(available_rasters={"frict_coef_file"})
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0
