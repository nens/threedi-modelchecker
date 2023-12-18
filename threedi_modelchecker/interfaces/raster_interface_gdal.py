from .raster_interface import RasterInterface

try:
    from osgeo import gdal, osr

    gdal.UseExceptions()
    osr.UseExceptions()
except ImportError:
    gdal = osr = None


class GDALRasterInterface(RasterInterface):
    def __init__(self, path):
        if gdal is None:
            raise ImportError("This raster check requires GDAL")
        super().__init__(path)

    @staticmethod
    def available():
        return gdal is not None

    def _open(self):
        try:
            self._dataset = gdal.Open(self.path, gdal.GA_ReadOnly)
        except RuntimeError:
            self._dataset = None

    def _close(self):
        self._dataset = None

    @property
    def _spatial_reference(self):
        dataset = self._dataset
        projection = None if dataset == None else dataset.GetProjection()
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
    def has_projection(self) -> bool:
        return self._spatial_reference is not None

    @property
    def is_geographic(self) -> bool:
        sr = self._spatial_reference
        return bool(sr.IsGeographic())

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
        try:
            return self._dataset.GetRasterBand(1).ComputeRasterMinMax(False)
        except RuntimeError as e:
            if "no valid pixels found" in str(e):
                raise self.NoData()
            else:
                raise e

    @property
    def shape(self):
        return (self._dataset.RasterYSize, self._dataset.RasterXSize)
