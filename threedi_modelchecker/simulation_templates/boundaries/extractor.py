from typing import List, Dict, Union
from threedi_modelchecker.threedi_model.models import (
    BoundaryConditions2D,
    BoundaryCondition1D,
)
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session
from threedi_modelchecker.simulation_templates.exceptions import SchematisationError
from threedi_modelchecker.simulation_templates.utils import parse_timeseries

# JSON format example:
# [
#     {
#         "interpolate": false,
#         "values": [
#             [0, 0.5],
#             [500, 0,8],
#             [1000, 0]
#         ]
#     },
#     {
#         "interpolate": false,
#         "values": [
#             [0, 0,3],
#             [400, 0.1]
#         ]
#     },
#     {
#         "interpolate": false,
#         "values": [
#             [0, -2.4],
#             [1300, 0,3],
#             [3000, 1.2],
#             [3600, 0]
#         ]
#     }
# ]
# 2D boundaries need to be provided before 1D boundaries.
# 1D boundaries need to be in order of connectionnode id's.
# 2D boundaries need to be in order of id (of the boundary).


def sqlite_boundary_to_dict(
    boundary: Union[BoundaryConditions2D, BoundaryCondition1D]
) -> Dict:
    try:
        values = parse_timeseries(boundary.timeseries)
    except (TypeError, ValueError):
        boundary_1d2d: str = "1d"
        if isinstance(boundary, BoundaryConditions2D):
            boundary_1d2d = "2d"
        raise SchematisationError(
            f"Incorrect formatted timeseries for {boundary_1d2d} boundary condition with id={boundary.id}"
        )

    return {"interpolate": False, "values": values}


class BoundariesExtractor(object):
    def __init__(self, session: Session):
        self.session = session
        self._boundaries_2d = None
        self._boundaries_1d = None

    @property
    def boundaries_2d(self) -> List[Dict]:
        if self._boundaries_2d is None:
            boundaries_2d = (
                Query(BoundaryConditions2D)
                .with_session(self.session)
                .order_by(BoundaryConditions2D.id)
                .all()
            )

            self._boundaries_2d = [sqlite_boundary_to_dict(x) for x in boundaries_2d]

        return self._boundaries_2d

    @property
    def boundaries_1d(self) -> List[Dict]:
        if self._boundaries_1d is None:
            boundaries_1d = (
                Query(BoundaryCondition1D)
                .with_session(self.session)
                .order_by(BoundaryCondition1D.connection_node_id)
                .all()
            )
            self._boundaries_1d = [sqlite_boundary_to_dict(x) for x in boundaries_1d]

        return self._boundaries_1d

    def as_list(self) -> List[Dict]:
        """
        Returns: list with dict's for every boundary, 2d boundaries before 1d boundaries
        """
        return self.boundaries_2d + self.boundaries_1d
