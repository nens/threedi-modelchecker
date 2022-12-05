from .raster_interface import RasterInterface
from .raster_interface_gdal import GDALRasterInterface
from typing import Optional
from typing import Type


def select_raster_interface() -> Optional[Type[RasterInterface]]:
    if GDALRasterInterface.available():
        return GDALRasterInterface
