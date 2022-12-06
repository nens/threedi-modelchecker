from .raster_interface import RasterInterface
from typing import Optional


try:
    import rasterio
except ImportError:
    rasterio = None


class RasterIORasterInterface(RasterInterface):
    def __init__(self, path):
        if rasterio is None:
            raise ImportError("This raster check requires rasterio")
        super().__init__(path)

    @staticmethod
    def available():
        return rasterio is not None

    def _open(self):
        with rasterio.Env(
            CPL_VSIL_CURL_USE_HEAD="NO",
            GDAL_DISABLE_READDIR_ON_OPEN="YES",
        ):
            try:
                self._dataset = rasterio.open(self.path, "r")
            except rasterio.RasterioIOError:
                self._dataset = None

    def _close(self):
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    @property
    def is_valid_geotiff(self):
        return self._dataset is not None and self._dataset.driver == "GTiff"

    @property
    def band_count(self):
        return self._dataset.count

    @property
    def is_geographic(self) -> Optional[bool]:
        return (
            self._dataset.crs.is_geographic if self._dataset.crs is not None else None
        )

    @property
    def epsg_code(self):
        return self._dataset.crs.to_epsg()

    @property
    def pixel_size(self):
        gt = self._dataset.get_transform()
        if gt is None:
            return None, None
        else:
            return abs(gt[1]), abs(gt[5])

    @property
    def min_max(self):
        if self.band_count == 0:
            return None, None
        statistics = self._dataset.statistics(1, approx=False, clear_cache=True)
        return statistics.min, statistics.max
