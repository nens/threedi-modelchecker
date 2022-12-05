from typing import Optional
from urllib.parse import urlencode


try:
    from osgeo import gdal
    from osgeo import osr

    gdal.UseExceptions()
    osr.UseExceptions()
except ImportError:
    gdal = osr = None


# https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access
VSICURL_SETTINGS = {
    "use_head": "no",
    "list_dir": "no",
    "max_retry": 3,
    "retry_delay": 1,
}


class RasterInterface:
    class NotAvailable(Exception):
        pass

    def __init__(self, path):
        if gdal is None:
            raise self.NotAvailable("This raster check requires GDAL")
        self.path = str(path)
        if self.uses_vsicurl and int(gdal.VersionInfo()[:3]) < 304:
            raise self.NotAvailable(
                "Checking rasters over HTTP requires at least GDAL 3.4"
            )

    @staticmethod
    def available():
        return gdal is not None

    @property
    def uses_vsicurl(self):
        return self.path.startswith("http://") or self.path.startswith("https://")

    @property
    def uri(self):
        # https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access
        if self.uses_vsicurl:
            return "/vsicurl?" + urlencode({"url": self.path, **VSICURL_SETTINGS})
        else:
            return self.path

    def __enter__(self) -> "RasterInterface":
        try:
            self._dataset = gdal.Open(self.uri, gdal.GA_ReadOnly)
        except RuntimeError:
            self._dataset = None
        return self

    def __exit__(self, *args, **kwargs):
        self._dataset = None

    @property
    def _spatial_reference(self):
        projection = self._dataset.GetProjection()
        if projection:
            return osr.SpatialReference(projection)

    @property
    def is_valid_geotiff(self):
        return (
            self._dataset is not None and self._dataset.GetDriver().ShortName == "GTiff"
        )

    @property
    def band_count(self):
        return self._dataset.RasterCount

    @property
    def is_geographic(self) -> Optional[bool]:
        sr = self._spatial_reference
        return None if sr is None else bool(sr.IsGeographic())

    @property
    def epsg_code(self):
        code = self._spatial_reference.GetAuthorityCode("PROJCS")
        return int(code) if code is not None else None

    @property
    def pixel_size(self):
        gt = self._dataset.GetGeoTransform()
        if gt is None:
            return None, None
        else:
            return abs(gt[1]), abs(gt[5])

    @property
    def min_max(self):
        if self.band_count == 0:
            return None, None
        # usage of approx_ok=False bypasses statistics cache and forces
        # all pixels to be read
        # see: https://gdal.org/doxygen/classGDALRasterBand.html#ac7761bab7cf3b8445ed963e4aa85e715
        return self._dataset.GetRasterBand(1).ComputeRasterMinMax(False)
