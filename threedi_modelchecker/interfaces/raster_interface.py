from abc import ABC, abstractmethod, abstractproperty, abstractstaticmethod
from typing import Optional, Tuple


class RasterInterface(ABC):
    class NotAvailable(Exception):
        pass

    class NoData(Exception):
        pass

    def __init__(self, path):
        self.path = str(path)

    @abstractstaticmethod
    def available():
        pass

    @abstractmethod
    def _open(self):
        pass

    @abstractmethod
    def _close(self):
        pass

    def __enter__(self) -> "RasterInterface":
        self._open()
        return self

    def __exit__(self, *args, **kwargs):
        self._close()

    @abstractproperty
    def is_valid_geotiff(self) -> bool:
        pass

    @abstractproperty
    def band_count(self) -> int:
        pass

    @abstractproperty
    def has_projection(self) -> bool:
        pass

    @abstractproperty
    def is_geographic(self) -> bool:
        pass

    @abstractproperty
    def epsg_code(self) -> Optional[int]:
        pass

    @abstractproperty
    def pixel_size(self) -> Tuple[Optional[float], Optional[float]]:
        gt = self._dataset.GetGeoTransform()
        if gt is None:
            return None, None
        else:
            return abs(gt[1]), abs(gt[5])

    @abstractproperty
    def min_max(self) -> Tuple[Optional[float], Optional[float]]:
        pass

    @abstractproperty
    def shape(self) -> Tuple[int, int]:
        pass
