from .base import BaseCheck
from dataclasses import dataclass
from pathlib import Path
from sqlalchemy import false
from typing import List
from typing import Set
from typing import Tuple


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

    def get_context(self, session) -> Context:
        return session.model_checker_context

    def get_paths(self, session, context: LocalContext) -> List[Tuple[int, Path]]:
        return [
            (x.id, Path(context.base_path / getattr(x, self.column.name)))
            for x in self.to_check(session).all()
        ]


class RasterExistsCheck(BaseRasterCheck):
    """Check whether a file referenced in given Column exists.

    In order to perform this check, the SQLAlchemy session requires a
    `model_checker_context` attribute, which is set automatically by the
    ThreediModelChecker and contains either a LocalContext or
    ServerContextinstance.
    """

    def none(self, session):
        return self.to_check(session).filter(false()).all()  # empty query

    def get_invalid(self, session):
        context = self.get_context(session)
        if isinstance(context, LocalContext):
            return self.get_invalid_local(session, context)
        else:
            return self.get_invalid_server(session, context)

    def get_invalid_local(self, session, context: LocalContext):
        invalid_ids = [
            x[0] for x in self.get_paths(session, context) if not x[1].exists()
        ]
        return self.to_check(session).filter(self.table.c.id.in_(invalid_ids)).all()

    def get_invalid_server(self, session, context: ServerContext):
        available_rasters = context.available_rasters
        if self.column.name in available_rasters:
            # the raster is available (so says the context)
            return self.none(session)
        else:
            # the raster is not available (so says the context)
            return self.to_check(session).all()

    def description(self):
        return f"The file in {self.column_name} is not present"
