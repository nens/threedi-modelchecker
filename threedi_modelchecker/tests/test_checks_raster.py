from unittest import mock

from threedi_schema import models

from threedi_modelchecker.checks.raster import (
    BaseRasterCheck,
    GDALAvailableCheck,
    LocalContext,
    RasterExistsCheck,
    RasterGridSizeCheck,
    RasterHasMatchingEPSGCheck,
    RasterHasOneBandCheck,
    RasterHasProjectionCheck,
    RasterIsProjectedCheck,
    RasterIsValidCheck,
    RasterPixelCountCheck,
    RasterRangeCheck,
    RasterSquareCellsCheck,
    ServerContext,
)
from threedi_modelchecker.interfaces.raster_interface_gdal import GDALRasterInterface
from threedi_modelchecker.interfaces.raster_interface_rasterio import (
    RasterIORasterInterface,
)

from . import factories

try:
    import numpy as np
    from osgeo import gdal, osr
except ImportError:
    gdal = osr = np = None

import pytest


@pytest.fixture
def mocked_check():
    with mock.patch.object(BaseRasterCheck, "is_valid", return_value=True):
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


def create_geotiff(
    path, epsg=28992, width=3, height=2, bands=1, dx=0.5, dy=0.5, value=None
):
    ds = gdal.GetDriverByName("GTiff").Create(
        str(path), width, height, bands, gdal.GDT_Byte
    )
    if epsg is not None:
        if isinstance(epsg, int):
            wkt = osr.GetUserInputAsWKT(f"EPSG:{epsg}")
        else:
            wkt = epsg
        ds.SetProjection(wkt)
    ds.SetGeoTransform((155000.0, dx, 0, 463000.0, 0, -dy))
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(255)
    if value is None:
        data = np.arange(height * width).reshape(height, width)
    else:
        data = np.full((height, width), fill_value=value, dtype=int)
    band.WriteArray(data)
    ds.FlushCache()
    return str(path)


@pytest.fixture
def valid_geotiff(tmp_path):
    return create_geotiff(tmp_path / "raster.tiff")


@pytest.fixture
def invalid_geotiff(tmp_path):
    path = tmp_path / "raster.tiff"
    path.touch()
    return str(path)


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


def test_base_get_invalid_local(mocked_check, session_local, invalid_geotiff):
    factories.GlobalSettingsFactory(dem_file="raster.tiff")
    assert mocked_check.get_invalid(session_local) == []
    mocked_check.is_valid.assert_called_once_with(
        invalid_geotiff, session_local.model_checker_context.raster_interface
    )


def test_base_get_invalid_local_no_file(mocked_check, session_local):
    factories.GlobalSettingsFactory(dem_file="somefile")
    assert mocked_check.get_invalid(session_local) == []
    assert not mocked_check.is_valid.called


def test_base_get_invalid_server(mocked_check, context_server, session_server):
    factories.GlobalSettingsFactory(dem_file="somefile")
    context_server.available_rasters = {"dem_file": "http://tempurl"}
    assert mocked_check.get_invalid(session_server) == []
    mocked_check.is_valid.assert_called_once_with(
        "http://tempurl", session_server.model_checker_context.raster_interface
    )


def test_base_get_invalid_server_no_file(mocked_check, context_server, session_server):
    factories.GlobalSettingsFactory(dem_file="somefile")
    context_server.available_rasters = {"other": "http://tempurl"}
    assert mocked_check.get_invalid(session_server) == []
    assert not mocked_check.is_valid.called


def test_base_get_invalid_server_available_set(
    mocked_check, context_server, session_server
):
    factories.GlobalSettingsFactory(dem_file="somefile")
    context_server.available_rasters = {"dem_file"}
    assert mocked_check.get_invalid(session_server) == []
    assert not mocked_check.is_valid.called


def test_base_no_gdal(mocked_check, session_local):
    with mock.patch.object(
        session_local.model_checker_context.raster_interface,
        "available",
        return_value=False,
    ):
        assert mocked_check.get_invalid(session_local) == []
        assert not mocked_check.is_valid.called


def test_exists_local_ok(session_local, invalid_geotiff):
    factories.GlobalSettingsFactory(dem_file="raster.tiff")
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    assert check.get_invalid(session_local) == []


def test_exists_local_err(session_local):
    factories.GlobalSettingsFactory(dem_file="raster.tiff")
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    assert len(check.get_invalid(session_local)) == 1


@pytest.mark.parametrize(
    "available_rasters", [{"dem_file": "http://tempurl"}, {"dem_file"}]
)
def test_exists_server_ok(session_server, context_server, available_rasters):
    factories.GlobalSettingsFactory(dem_file="raster.tiff")
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    context_server.available_rasters = available_rasters
    assert check.get_invalid(session_server) == []


@pytest.mark.parametrize("available_rasters", [{"other": "http://tempurl"}, {"other"}])
def test_exists_server_err(session_server, context_server, available_rasters):
    factories.GlobalSettingsFactory(dem_file="raster.tiff")
    check = RasterExistsCheck(column=models.GlobalSetting.dem_file)
    context_server.available_rasters = available_rasters
    assert len(check.get_invalid(session_server)) == 1


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_valid_ok(valid_geotiff, interface_cls):
    check = RasterIsValidCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid(valid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_valid_err(invalid_geotiff, interface_cls):
    check = RasterIsValidCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid(invalid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_one_band_ok(valid_geotiff, interface_cls):
    check = RasterHasOneBandCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid(valid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_one_band_err(tmp_path, interface_cls):
    path = create_geotiff(tmp_path / "raster.tiff", bands=2)
    check = RasterHasOneBandCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid(path, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_has_projection_ok(valid_geotiff, interface_cls):
    check = RasterHasProjectionCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid(valid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_has_projection_err(tmp_path, interface_cls):
    path = create_geotiff(tmp_path / "raster.tiff", epsg=None)
    check = RasterHasProjectionCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid(path, interface_cls)


NULL_EPSG_CODE = (
    'PROJCS["unnamed",GEOGCS["GRS 1980(IUGG, 1980)"'
    + ',DATUM["unknown",SPHEROID["GRS80",6378137,298.257222101]],'
    + 'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],'
    + 'PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",-18],'
    + 'PARAMETER["standard_parallel_2",-36],PARAMETER["latitude_of_center",-33.264],'
    + 'PARAMETER["longitude_of_center",150.874],PARAMETER["false_easting",0],'
    + 'PARAMETER["false_northing",0],UNIT["kilometre",1000]]'
)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
@pytest.mark.parametrize(
    "raster_epsg, sqlite_epsg, validity",
    [
        (28992, 28992, True),
        (28992, 27700, False),
        (NULL_EPSG_CODE, 28992, False),
        (27700, None, False),
    ],
)
def test_has_epsg(tmp_path, interface_cls, raster_epsg, sqlite_epsg, validity):
    path = create_geotiff(tmp_path / "raster.tiff", epsg=raster_epsg)
    check = RasterHasMatchingEPSGCheck(column=models.GlobalSetting.dem_file)
    check.epsg_code = sqlite_epsg
    assert check.is_valid(path, interface_cls) == validity


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_is_projected_ok(valid_geotiff, interface_cls):
    check = RasterIsProjectedCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid(valid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_is_projected_err(tmp_path, interface_cls):
    path = create_geotiff(tmp_path / "raster.tiff", epsg=4326)
    check = RasterIsProjectedCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid(path, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_is_projected_no_projection(tmp_path, interface_cls):
    path = create_geotiff(tmp_path / "raster.tiff", epsg=None)
    check = RasterIsProjectedCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid(path, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_square_cells_ok(valid_geotiff, interface_cls):
    check = RasterSquareCellsCheck(column=models.GlobalSetting.dem_file)
    assert check.is_valid(valid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_square_cells_err(tmp_path, interface_cls):
    path = create_geotiff(tmp_path / "raster.tiff", dx=0.5, dy=1.0)
    check = RasterSquareCellsCheck(column=models.GlobalSetting.dem_file)
    assert not check.is_valid(path, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_square_cells_rounding(tmp_path, interface_cls):
    path = create_geotiff(tmp_path / "raster.tiff", dx=0.5, dy=0.5001)
    check = RasterSquareCellsCheck(decimals=3, column=models.GlobalSetting.dem_file)
    assert check.is_valid(path, interface_cls)
    check = RasterSquareCellsCheck(decimals=4, column=models.GlobalSetting.dem_file)
    assert not check.is_valid(path, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
@pytest.mark.parametrize(
    "raster_pixel_size, sqlite_grid_space, validity",
    [
        (2, 7, False),
        (2, 4, True),
        (2, 3, False),
        (2, 0, False),
        (2, -4, False),
        (2, 7.9999999999999999, True),
    ],
)
def test_raster_grid_size(
    tmp_path, interface_cls, raster_pixel_size, sqlite_grid_space, validity
):
    path = create_geotiff(
        tmp_path / "raster.tiff", dx=raster_pixel_size, dy=raster_pixel_size
    )
    check = RasterGridSizeCheck(column=models.GlobalSetting.dem_file)
    check.grid_space = sqlite_grid_space
    assert check.is_valid(path, interface_cls) == validity


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
@pytest.mark.parametrize(
    "pixel_count_side, validity",
    [
        (4, True),  # total less than threshold
        (5, True),  # total equal to threshold
        (6, False),  # total more than threshold
    ],
)
def test_raster_pixel_count(tmp_path, interface_cls, pixel_count_side, validity):
    path = create_geotiff(
        tmp_path / "raster.tiff",
        width=pixel_count_side,
        height=pixel_count_side,
        dx=pixel_count_side,
        dy=pixel_count_side,
    )
    # max_pixels is x pixels times y pixels
    check = RasterPixelCountCheck(column=models.GlobalSetting.dem_file, max_pixels=25)
    assert check.is_valid(path, interface_cls) == validity


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_raster_range_ok(valid_geotiff, interface_cls):
    check = RasterRangeCheck(
        column=models.GlobalSetting.dem_file, min_value=0, max_value=5
    )
    assert check.is_valid(valid_geotiff, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
@pytest.mark.parametrize(
    "kwargs,msg",
    [
        ({"min_value": 1}, "{} has values <1 or is empty"),
        ({"max_value": 4}, "{} has values >4 or is empty"),
        ({"min_value": 0, "left_inclusive": False}, "{} has values <=0 or is empty"),
        ({"max_value": 5, "right_inclusive": False}, "{} has values >=5 or is empty"),
        ({"min_value": 1, "max_value": 6}, "{} has values <1 and/or >6 or is empty"),
    ],
)
def test_raster_range_err(valid_geotiff, kwargs, msg, interface_cls):
    check = RasterRangeCheck(column=models.GlobalSetting.dem_file, **kwargs)
    assert not check.is_valid(valid_geotiff, interface_cls)
    assert check.description() == msg.format("v2_global_settings.dem_file")


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
def test_raster_range_no_data(tmp_path, interface_cls):
    path = tmp_path / "raster.tiff"
    create_geotiff(path, value=255)
    check = RasterRangeCheck(column=models.GlobalSetting.dem_file, min_value=0)
    assert not check.is_valid(path, interface_cls)


@pytest.mark.parametrize(
    "interface_cls", [GDALRasterInterface, RasterIORasterInterface]
)
@pytest.mark.parametrize(
    "check",
    [
        RasterHasOneBandCheck(column=models.GlobalSetting.dem_file),
        RasterHasProjectionCheck(column=models.GlobalSetting.dem_file),
        RasterHasMatchingEPSGCheck(column=models.GlobalSetting.dem_file),
        RasterIsProjectedCheck(column=models.GlobalSetting.dem_file),
        RasterSquareCellsCheck(column=models.GlobalSetting.dem_file),
        RasterGridSizeCheck(column=models.GlobalSetting.dem_file),
        RasterRangeCheck(column=models.GlobalSetting.dem_file, min_value=0),
    ],
)
def test_raster_check_invalid_file(check, invalid_geotiff, interface_cls):
    assert check.is_valid(invalid_geotiff, interface_cls)


def test_gdal_check_ok(session_local):
    check = GDALAvailableCheck(column=models.GlobalSetting.dem_file)
    assert not check.get_invalid(session_local)


def test_gdal_check_err(session_local):
    with mock.patch.object(
        session_local.model_checker_context.raster_interface,
        "available",
        return_value=False,
    ):
        check = GDALAvailableCheck(column=models.GlobalSetting.dem_file)
        assert check.get_invalid(session_local)
