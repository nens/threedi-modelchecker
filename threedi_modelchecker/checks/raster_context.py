from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Type

from threedi_modelchecker.interfaces import GDALRasterInterface, RasterInterface


class Context:
    pass


@dataclass
class ServerContext(Context):
    available_rasters: Dict[str, str]
    raster_interface: Type[RasterInterface] = GDALRasterInterface


@dataclass
class LocalContext(Context):
    base_path: Path
    raster_interface: Type[RasterInterface] = GDALRasterInterface
