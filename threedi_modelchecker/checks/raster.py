from .base import BaseCheck
from dataclasses import dataclass
from pathlib import Path
from threedi_modelchecker.interfaces import RasterInterface
from typing import Set


class Context:
    pass


@dataclass
class ServerContext(Context):
    available_rasters: Set[str]


@dataclass
class LocalContext(Context):
    base_path: Path


class BaseRasterCheck(BaseCheck):
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
        if isinstance(context, LocalContext):
            is_valid = self.is_valid_local
        elif isinstance(context, ServerContext):
            is_valid = self.is_valid_server
        else:
            raise NotImplementedError(f"Invalid context type: {context}")

        column_name = self.column.name
        return [
            x
            for x in self.to_check(session).all()
            if not is_valid(getattr(x, column_name), context)
        ]

    def is_valid_local(self, rel_path: str, context: LocalContext):
        return True

    def is_valid_server(self, rel_path: str, context: ServerContext):
        return True


class RasterExistsCheck(BaseRasterCheck):
    """Check whether a file referenced in given Column exists.

    In order to perform this check, the SQLAlchemy session requires a
    `model_checker_context` attribute, which is set automatically by the
    ThreediModelChecker and contains either a LocalContext or
    ServerContextinstance.
    """

    def is_valid_local(self, rel_path: str, context: LocalContext):
        return Path(context.base_path / rel_path).exists()

    def is_valid_server(self, rel_path: str, context: ServerContext):
        return self.column.name in context.available_rasters

    def description(self):
        return f"The file in {self.column_name} is not present"


class RasterIsValidCheck(BaseRasterCheck):
    """Check whether a file is a geotiff.

    Only works locally.
    """

    def is_valid_local(self, rel_path: str, context: LocalContext):
        path = Path(context.base_path / rel_path)
        if not path.exists():
            return True  # RasterExistsCheck will cover this situation
        with RasterInterface(path) as raster:
            return raster.is_valid_geotiff

    def description(self):
        return f"The file in {self.column_name} is not a valid GeoTIFF file"


class RasterHasOneBandCheck(BaseRasterCheck):
    """Check whether a raster has a single band.

    Only works locally.
    """

    def is_valid_local(self, rel_path: str, context: LocalContext):
        with RasterInterface(Path(context.base_path / rel_path)) as raster:
            if not raster.is_valid_geotiff:
                return True
            return raster.band_count == 1

    def description(self):
        return f"The file in {self.column_name} has multiple or no bands."


class RasterIsProjectedCheck(BaseRasterCheck):
    """Check whether a raster has a projected coordinate system.

    Only works locally.
    """

    def is_valid_local(self, rel_path: str, context: LocalContext):
        with RasterInterface(Path(context.base_path / rel_path)) as raster:
            if not raster.is_valid_geotiff:
                return True
            return raster.is_geographic is False

    def description(self):
        return f"The file in {self.column_name} does not use a projected CRS."


class RasterSquareCellsCheck(BaseRasterCheck):
    """Check whether a raster has square cells (pixels)

    Only works locally.
    """

    def is_valid_local(self, rel_path: str, context: LocalContext):
        with RasterInterface(Path(context.base_path / rel_path)) as raster:
            if not raster.is_valid_geotiff:
                return True
            dx, dy = raster.pixel_size
            return dx is not None and dx == dy

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

    def is_valid_local(self, rel_path: str, context: LocalContext):
        with RasterInterface(Path(context.base_path / rel_path)) as raster:
            if not raster.is_valid_geotiff:
                return True
            raster_min = raster.min_value
            raster_max = raster.max_value

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
