from typing import Optional


try:
    from osgeo import gdal
    from osgeo import osr

    gdal.UseExceptions()
    osr.UseExceptions()
except ImportError:
    gdal = osr = None


class RasterInterface:
    def __init__(self, path):
        if gdal is None:
            raise ImportError("This raster check requires GDAL")
        self.path = str(path)

    @staticmethod
    def available():
        return gdal is not None

    def __enter__(self) -> "RasterInterface":
        try:
            self._dataset = gdal.OpenEx(
                self.path, gdal.GA_ReadOnly, allowed_drivers=["gtiff"]
            )
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
        return self._dataset is not None

    @property
    def band_count(self):
        return self._dataset.RasterCount

    @property
    def is_geographic(self) -> Optional[bool]:
        sr = self._spatial_reference
        return None if sr is None else bool(sr.IsGeographic())

    @property
    def epsg_code(self):
        if not self.is_geographic:
            return None
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