from tests import factories
from threedi_modelchecker.checks.raster import BaseRasterCheck
from threedi_modelchecker.checks.raster import GDALAvailableCheck
from threedi_modelchecker.checks.raster import LocalContext
from threedi_modelchecker.checks.raster import RasterExistsCheck
from threedi_modelchecker.checks.raster import RasterHasOneBandCheck
from threedi_modelchecker.checks.raster import RasterHasProjectionCheck
from threedi_modelchecker.checks.raster import RasterIsProjectedCheck
from threedi_modelchecker.checks.raster import RasterIsValidCheck
from threedi_modelchecker.checks.raster import RasterRangeCheck
from threedi_modelchecker.checks.raster import RasterSquareCellsCheck
from threedi_modelchecker.checks.raster import ServerContext
from threedi_modelchecker.threedi_model import models
from unittest import mock


try:
    from osgeo import gdal
    from osgeo import osr

    import numpy as np
except ImportError:
    gdal = osr = np = None

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


def test_exists_local_ok(context_local, tmp_path):
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    (tmp_path / "somefile").touch()
    assert check.is_valid_local("somefile", context_local)


def test_exists_local_err(context_local):
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("somefile", context_local)


def test_exists_server_ok(context_server):
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    context_server.available_rasters = {"dem_file"}
    assert check.is_valid_server("somefile", context_server)


def test_exists_erver_err(context_server):
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    context_server.available_rasters = {"other"}
    assert not check.is_valid_server("somefile", context_server)


def create_geotiff(path, epsg=28992, width=3, height=2, bands=1, dx=0.5, dy=0.5):
    ds = gdal.GetDriverByName("GTiff").Create(
        str(path), width, height, bands, gdal.GDT_Byte
    )
    if epsg is not None:
        ds.SetProjection(osr.GetUserInputAsWKT(f"EPSG:{epsg}"))
    ds.SetGeoTransform((155000.0, dx, 0, 463000.0, 0, -dy))
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(255)
    band.WriteArray(np.arange(height * width).reshape(height, width))
    ds.FlushCache()


@pytest.fixture
def valid_geotiff(tmp_path):
    create_geotiff(tmp_path / "raster.tiff")
    return "raster.tiff"


def test_valid_ok(context_local, valid_geotiff):
    check = RasterIsValidCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid_local(valid_geotiff, context_local)


def test_valid_err(context_local, tmp_path):
    (tmp_path / "somefile.tiff").touch()
    check = RasterIsValidCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("somefile.tiff", context_local)


def test_one_band_ok(context_local, valid_geotiff):
    check = RasterHasOneBandCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid_local(valid_geotiff, context_local)


def test_one_band_err(context_local, tmp_path):
    create_geotiff(tmp_path / "raster.tiff", bands=2)
    check = RasterHasOneBandCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("raster.tiff", context_local)


def test_has_projection_ok(context_local, valid_geotiff):
    check = RasterHasProjectionCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid_local(valid_geotiff, context_local)


def test_has_projection_err(context_local, tmp_path):
    create_geotiff(tmp_path / "raster.tiff", epsg=None)
    check = RasterHasProjectionCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("raster.tiff", context_local)


def test_is_projected_ok(context_local, valid_geotiff):
    check = RasterIsProjectedCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid_local(valid_geotiff, context_local)


def test_is_projected_err(context_local, tmp_path):
    create_geotiff(tmp_path / "raster.tiff", epsg=4326)
    check = RasterIsProjectedCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("raster.tiff", context_local)


def test_is_projected_no_projection(context_local, tmp_path):
    create_geotiff(tmp_path / "raster.tiff", epsg=None)
    check = RasterIsProjectedCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid_local("raster.tiff", context_local)


def test_square_cells_ok(context_local, valid_geotiff):
    check = RasterSquareCellsCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid_local(valid_geotiff, context_local)


def test_square_cells_err(context_local, tmp_path):
    create_geotiff(tmp_path / "raster.tiff", dx=0.5, dy=1.0)
    check = RasterSquareCellsCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("raster.tiff", context_local)


def test_square_cells_rounding(context_local, tmp_path):
    create_geotiff(tmp_path / "raster.tiff", dx=0.5, dy=0.5001)
    check = RasterSquareCellsCheck(decimals=3, column=models.GlobalSetting.dem_file)
    assert check.is_valid_local("raster.tiff", context_local)
    check = RasterSquareCellsCheck(decimals=4, column=models.GlobalSetting.dem_file)
    assert not check.is_valid_local("raster.tiff", context_local)


def test_raster_range_ok(context_local, valid_geotiff):
    check = RasterRangeCheck(
        column=models.GlobalSetting.dem_file, min_value=0, max_value=5
    )
    assert check.is_valid_local(valid_geotiff, context_local)


@pytest.mark.parametrize(
    "kwargs,msg",
    [
        ({"min_value": 1}, "{} has values <1"),
        ({"max_value": 4}, "{} has values >4"),
        ({"min_value": 0, "left_inclusive": False}, "{} has values <=0"),
        ({"max_value": 5, "right_inclusive": False}, "{} has values >=5"),
        ({"min_value": 1, "max_value": 6}, "{} has values <1 and/or >6"),
    ],
)
def test_raster_range_err(context_local, valid_geotiff, kwargs, msg):
    check = RasterRangeCheck(column=models.GlobalSetting.dem_file, **kwargs)
    assert not check.is_valid_local(valid_geotiff, context_local)
    assert check.description() == msg.format("v2_global_settings.dem_file")


@pytest.mark.parametrize(
    "check",
    [
        RasterIsValidCheck(column=models.GlobalSetting.dem_file),
        RasterHasOneBandCheck(column=models.GlobalSetting.dem_file),
        RasterHasProjectionCheck(column=models.GlobalSetting.dem_file),
        RasterIsProjectedCheck(column=models.GlobalSetting.dem_file),
        RasterSquareCellsCheck(column=models.GlobalSetting.dem_file),
        RasterRangeCheck(column=models.GlobalSetting.dem_file, min_value=0),
    ],
)
def test_raster_check_file_missing(check, context_local):
    assert check.is_valid_local("somefile.tiff", context_local)


@pytest.mark.parametrize(
    "check",
    [
        RasterHasOneBandCheck(column=models.GlobalSetting.dem_file),
        RasterHasProjectionCheck(column=models.GlobalSetting.dem_file),
        RasterIsProjectedCheck(column=models.GlobalSetting.dem_file),
        RasterSquareCellsCheck(column=models.GlobalSetting.dem_file),
        RasterRangeCheck(column=models.GlobalSetting.dem_file, min_value=0),
    ],
)
def test_raster_check_invalid_file(check, context_local, tmp_path):
    (tmp_path / "somefile.tiff").touch()
    assert check.is_valid_local("somefile.tiff", context_local)


@mock.patch("threedi_modelchecker.interfaces.raster_interface.gdal", new=None)
@pytest.mark.parametrize(
    "check",
    [
        RasterIsValidCheck(column=models.GlobalSetting.dem_file),
        RasterHasOneBandCheck(column=models.GlobalSetting.dem_file),
        RasterHasProjectionCheck(column=models.GlobalSetting.dem_file),
        RasterIsProjectedCheck(column=models.GlobalSetting.dem_file),
        RasterSquareCellsCheck(column=models.GlobalSetting.dem_file),
        RasterRangeCheck(column=models.GlobalSetting.dem_file, min_value=0),
    ],
)
def test_raster_check_no_gdal(check, context_local, tmp_path):
    (tmp_path / "somefile.tiff").touch()
    assert check.is_valid_local("somefile.tiff", context_local)


def test_gdal_check_ok(session_local):
    check = GDALAvailableCheck(column=models.GlobalSetting.dem_file)
    assert not check.get_invalid(session_local)


@mock.patch("threedi_modelchecker.interfaces.raster_interface.gdal", new=None)
def test_gdal_check_err(session_local):
    check = GDALAvailableCheck(column=models.GlobalSetting.dem_file)
    assert check.get_invalid(session_local)
