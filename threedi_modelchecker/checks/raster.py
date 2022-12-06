from .base import BaseCheck
from dataclasses import dataclass
from pathlib import Path
from threedi_modelchecker.interfaces import GDALRasterInterface
from threedi_modelchecker.interfaces import RasterInterface
from typing import Optional
from typing import Set
from typing import Type


class Context:
    pass


@dataclass
class ServerContext(Context):
    available_rasters: Set[str]
    raster_interface: Type[RasterInterface] = GDALRasterInterface


@dataclass
class LocalContext(Context):
    base_path: Path
    raster_interface: Type[RasterInterface] = GDALRasterInterface


class BaseRasterCheck(BaseCheck):
    """Baseclass for all raster checks.

    Because these checks are different on local and server systems, subclasses may
    implement 2 methods: is_valid_local and/or is_valid_local.
    """

    def to_check(self, session):
        return (
            super()
            .to_check(session)
            .filter(
                self.column != None,
                self.column != "",
            )
        )

    def get_invalid(self, session):
        context = session.model_checker_context
        raster_interface = context.raster_interface
        if not raster_interface.available():
            return []
        if isinstance(context, ServerContext):
            # max 1 record; we can only have 1 raster per type on the server
            records = list(self.to_check(session).limit(1).all())
            paths = [self.get_path_server(x, context) for x in records]
        else:
            records = list(self.to_check(session).all())
            paths = [self.get_path_local(x, context) for x in records]
        return [
            record
            for (record, path) in zip(records, paths)
            if path is not None and not self.is_valid(path, raster_interface)
        ]

    def get_path_local(self, record, context: LocalContext) -> Optional[str]:
        abs_path = context.base_path / getattr(record, self.column.name)
        if abs_path.exists():
            return str(abs_path)

    def get_path_server(self, record, context: ServerContext) -> str:
        if isinstance(context.available_rasters, dict):
            return context.available_rasters.get(self.column.name)

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        return True


class RasterExistsCheck(BaseRasterCheck):
    """Check whether a file referenced in given Column exists.

    In order to perform this check, the SQLAlchemy session requires a
    `model_checker_context` attribute, which is set automatically by the
    ThreediModelChecker and contains either a LocalContext or
    ServerContextinstance.
    """

    def get_invalid(self, session):
        context = session.model_checker_context
        if isinstance(context, ServerContext):
            if self.column.name in context.available_rasters:
                return []
            else:
                return self.to_check(session).all()
        else:
            records = list(self.to_check(session).all())
            paths = [self.get_path_local(x, context) for x in records]
            return [record for (record, path) in zip(records, paths) if path is None]

    def description(self):
        return f"The file in {self.column_name} is not present"


class RasterIsValidCheck(BaseRasterCheck):
    """Check whether a file is a geotiff.

    Only works locally.
    """

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        with interface_cls(path) as raster:
            return raster.is_valid_geotiff

    def description(self):
        return f"The file in {self.column_name} is not a valid GeoTIFF file"


class RasterHasOneBandCheck(BaseRasterCheck):
    """Check whether a raster has a single band.

    Only works locally.
    """

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        with interface_cls(path) as raster:
            if not raster.is_valid_geotiff:
                return True
            return raster.band_count == 1

    def description(self):
        return f"The file in {self.column_name} has multiple or no bands."


class RasterHasProjectionCheck(BaseRasterCheck):
    """Check whether a raster has a projected coordinate system.

    Only works locally.
    """

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        with interface_cls(path) as raster:
            if not raster.is_valid_geotiff:
                return True
            return raster.is_geographic is not None

    def description(self):
        return f"The file in {self.column_name} has no CRS."


class RasterIsProjectedCheck(BaseRasterCheck):
    """Check whether a raster has a projected coordinate system.

    Only works locally.
    """

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        with interface_cls(path) as raster:
            if not raster.is_valid_geotiff:
                return True
            return raster.is_geographic is not True

    def description(self):
        return f"The file in {self.column_name} does not use a projected CRS."


class RasterSquareCellsCheck(BaseRasterCheck):
    """Check whether a raster has square cells (pixels)

    Only works locally.
    """

    def __init__(self, *args, decimals=7, **kwargs):
        super().__init__(*args, **kwargs)
        self.decimals = decimals

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        with interface_cls(path) as raster:
            if not raster.is_valid_geotiff:
                return True
            dx, dy = raster.pixel_size
            return dx is not None and round(dx, self.decimals) == round(
                dy, self.decimals
            )

    def description(self):
        return f"The raster in {self.column_name} has non-square raster cells."


class RasterRangeCheck(BaseRasterCheck):
    """Check whether a raster has values outside of provided range.

    Also fails when there are no values in the raster. Only works locally.
    """

    def __init__(
        self,
        min_value=None,
        max_value=None,
        left_inclusive=True,
        right_inclusive=True,
        message=None,
        *args,
        **kwargs,
    ):
        if min_value is None and max_value is None:
            raise ValueError("Please supply at least one of {min_value, max_value}.")
        self.min_value = min_value
        self.max_value = max_value
        self.left_inclusive = left_inclusive
        self.right_inclusive = right_inclusive
        self.message = message
        super().__init__(*args, **kwargs)

    def is_valid(self, path: str, interface_cls: Type[RasterInterface]):
        with interface_cls(path) as raster:
            if not raster.is_valid_geotiff:
                return True
            raster_min, raster_max = raster.min_max

        if raster_min is None or raster_max is None:
            return False
        if self.min_value is not None:
            if self.left_inclusive and raster_min < self.min_value:
                return False
            if not self.left_inclusive and raster_min <= self.min_value:
                return False
        if self.max_value is not None:
            if self.right_inclusive and raster_max > self.max_value:
                return False
            if not self.right_inclusive and raster_max >= self.max_value:
                return False

        return True

    def description(self):
        if self.message:
            return self.message
        parts = []
        if self.min_value is not None:
            parts.append(f"{'<' if self.left_inclusive else '<='}{self.min_value}")
        if self.max_value is not None:
            parts.append(f"{'>' if self.right_inclusive else '>='}{self.max_value}")
        return f"{self.column_name} has values {' and/or '.join(parts)}"


@dataclass
class GDALUnavailable:
    id: int


class GDALAvailableCheck(BaseRasterCheck):
    """Checks whether GDAL is available"""

    def get_invalid(self, session):
        context = session.model_checker_context
        raster_interface = context.raster_interface
        if not raster_interface.available():
            return [GDALUnavailable(id=1)]
        else:
            return []

    def description(self) -> str:
        return "raster checks require GDAL to be available"
