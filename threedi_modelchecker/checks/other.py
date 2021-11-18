from ..threedi_model import constants
from ..threedi_model import models
from .base import BaseCheck
from .base import CheckLevel
from geoalchemy2 import functions as geo_func
from sqlalchemy import func
from sqlalchemy import text
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Query
from sqlalchemy.orm import Session
from threedi_modelchecker.checks import patterns
from typing import List
from typing import NamedTuple


class BankLevelCheck(BaseCheck):
    """Check 'CrossSectionLocation.bank_level' is not null if
    calculation_type is CONNECTED or DOUBLE_CONNECTED.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionLocation.bank_level, *args, **kwargs)

    def get_invalid(self, session):
        q = session.query(self.table).filter(
            models.CrossSectionLocation.bank_level == None,
            models.CrossSectionLocation.channel.has(
                models.Channel.calculation_type.in_(
                    [
                        constants.CalculationType.CONNECTED,
                        constants.CalculationType.DOUBLE_CONNECTED,
                    ]
                )
            ),
        )
        return q.all()

    def description(self):
        return (
            "CrossSectionLocation.bank_level cannot be NULL when calculation_type "
            "is CONNECTED or DOUBLE_CONNECTED"
        )


class CrossSectionLocationCheck(BaseCheck):
    """Check if cross section locations are within {max_distance} of their channel."""

    def __init__(self, max_distance, *args, **kwargs):
        super().__init__(column=models.CrossSectionLocation.the_geom, *args, **kwargs)
        self.max_distance = max_distance

    def get_invalid(self, session):
        epsg_code = Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code")
        return (
            self.to_check(session)
            .join(models.Channel)
            .filter(
                geo_func.ST_Distance(
                    geo_func.ST_Transform(
                        models.CrossSectionLocation.the_geom, epsg_code
                    ),
                    geo_func.ST_Transform(models.Channel.the_geom, epsg_code),
                )
                > self.max_distance
            )
            .all()
        )

    def description(self):
        return "v2_cross_section_location.the_geom is invalid: the cross-section location should be located on the channel geometry"


class TimeseriesCheck(BaseCheck):
    """Check that `column` has the time series pattern: digit,float\n

    The first digit is the timestep in minutes, the float is a value depending
    on the type of timeseries.

    Example of a timeserie: 0,-0.5\n59,-0.5\n60,-0.5\n61,-0.5\n9999,-0.5

    All timeseries in the table should contain the same timesteps.
    """

    def get_invalid(self, session):
        invalid_timeseries = []
        required_timesteps = {}
        rows = session.query(self.table).all()

        for row in rows:
            timeserie = row.timeseries
            if not patterns.TIMESERIES_REGEX.fullmatch(timeserie):
                invalid_timeseries.append(row)
                continue

            timesteps = {
                time for time, *_ in patterns.TIMESERIE_ENTRY_REGEX.findall(timeserie)
            }
            if not required_timesteps:
                # Assume the first timeserie defines the required timesteps.
                # All others should have the same timesteps.
                required_timesteps = timesteps
                continue
            if timesteps != required_timesteps:
                invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return f"{self.column} contains an invalid timeseries"


class Use0DFlowCheck(BaseCheck):
    """Check that when use_0d_flow in global settings is configured to 1 or to
    2, there is at least one impervious surface or surfaces respectively.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.GlobalSetting.use_0d_inflow, *args, **kwargs)

    def to_check(self, session):
        """Return a Query object on which this check is applied"""
        return session.query(models.GlobalSetting).filter(
            models.GlobalSetting.use_0d_inflow != 0
        )

    def get_invalid(self, session):
        surface_count = session.query(func.count(models.Surface.id)).scalar()
        impervious_surface_count = session.query(
            func.count(models.ImperviousSurface.id)
        ).scalar()

        invalid_rows = []
        for row in self.to_check(session):
            if (
                row.use_0d_inflow == constants.InflowType.IMPERVIOUS_SURFACE
                and impervious_surface_count == 0
            ):
                invalid_rows.append(row)
            elif (
                row.use_0d_inflow == constants.InflowType.SURFACE and surface_count == 0
            ):
                invalid_rows.append(row)
            else:
                continue
        return invalid_rows

    def description(self):
        return (
            "When %s is used, there should exist at least one "
            "(impervious) surface." % self.column
        )


class ConnectionNodes(BaseCheck):
    """Check that all connection nodes are connected to at least one of the
    following objects:
    - Culvert
    - Channel
    - Pipe
    - Orifice
    - Pumpstation
    - Weir
    """

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)

    def get_invalid(self, session):
        raise NotImplementedError


class ConnectionNodesLength(BaseCheck):
    """Check that the distance between `start_node` and `end_node` is at least
    `min_distance`. The coords will be transformed into (the first entry) of
    GlobalSettings.epsg_code. The `min_distance` will be interpreted as these units.
    For example epsg:28992 will be in meters while epsg:4326 is in degrees."""

    def __init__(self, start_node, end_node, min_distance: float, *args, **kwargs):
        """

        :param start_node: column name of the start node
        :param end_node: column name of the end node
        :param min_distance: minimum required distance between start and end node
        """
        super().__init__(*args, **kwargs)
        self.start_node = start_node
        self.end_node = end_node
        self.min_distance = min_distance

    def get_invalid(self, session):
        start_node = aliased(models.ConnectionNode)
        end_node = aliased(models.ConnectionNode)
        epsg_code = Query(models.GlobalSetting.epsg_code).limit(1).label("epsg_code")
        q = (
            Query(self.column.class_)
            .join(start_node, self.start_node)
            .join(end_node, self.end_node)
            .filter(
                geo_func.ST_Distance(
                    geo_func.ST_Transform(start_node.the_geom, epsg_code),
                    geo_func.ST_Transform(end_node.the_geom, epsg_code),
                )
                < self.min_distance
            )
        )
        return list(q.with_session(session).all())

    def description(self) -> str:
        return (
            f"The length of {self.table} is "
            f"very short (< {self.min_distance}). A length of at least 1.0 m is recommended."
        )


class ConnectionNodesDistance(BaseCheck):
    """Check that the distance between CONNECTED connection nodes is above a certain
    threshold
    """

    def __init__(self, minimum_distance: float, *args, **kwargs):
        """
        :param minimum_distance: threshold distance in meters
        """
        super().__init__(
            column=models.ConnectionNode.id, level=CheckLevel.WARNING, *args, **kwargs
        )
        self.minimum_distance = minimum_distance

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        """
        The query makes use of the SpatialIndex so we won't have to calculate the
        distance between all connection nodes.

        The query only works on a spatialite and therefore skips postgres.
        """
        if session.bind.name == "postgresql":
            return []

        check_spatial_index = (
            "SELECT CheckSpatialIndex('v2_connection_nodes', 'the_geom')"
        )
        if not session.connection().execute(check_spatial_index).scalar():
            recover_spatial_index = (
                "SELECT RecoverSpatialIndex('v2_connection_nodes', 'the_geom')"
            )
            session.connection().execute(recover_spatial_index).scalar()

        query = text(
            f"""SELECT *
               FROM v2_connection_nodes AS cn1, v2_connection_nodes AS cn2
               WHERE
                   distance(cn1.the_geom, cn2.the_geom, 1) < :min_distance
                   AND cn1.ROWID != cn2.ROWID
                   AND cn2.ROWID IN (
                     SELECT ROWID
                     FROM SpatialIndex
                     WHERE (
                       f_table_name = "v2_connection_nodes"
                       AND search_frame = Buffer(cn1.the_geom, {self.minimum_distance / 2})));
            """
        )
        results = (
            session.connection()
            .execute(query, min_distance=self.minimum_distance)
            .fetchall()
        )

        return results

    def description(self) -> str:
        return (
            f"The connection_node is within {self.minimum_distance} meters of "
            f"another connection_node."
        )


class OpenChannelsWithNestedNewton(BaseCheck):
    """Checks whether the model has any closed cross-section in use when the
    NumericalSettings.use_of_nested_newton is turned off.

    See https://github.com/nens/threeditoolbox/issues/522
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            column=models.CrossSectionDefinition.id,
            level=CheckLevel.WARNING,
            filters=Query(models.NumericalSettings)
            .filter(models.NumericalSettings.use_of_nested_newton == 0)
            .exists(),
            *args,
            **kwargs,
        )

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        definitions_in_use = self.to_check(session).filter(
            models.CrossSectionDefinition.id.in_(
                Query(models.CrossSectionLocation.definition_id).union_all(
                    Query(models.Pipe.cross_section_definition_id),
                    Query(models.Culvert.cross_section_definition_id),
                    Query(models.Weir.cross_section_definition_id),
                    Query(models.Orifice.cross_section_definition_id),
                )
            ),
        )

        # closed_rectangle, circle, and egg cross-section definitions are always closed:
        closed_definitions = definitions_in_use.filter(
            models.CrossSectionDefinition.shape.in_(
                [
                    constants.CrossSectionShape.CLOSED_RECTANGLE,
                    constants.CrossSectionShape.CIRCLE,
                    constants.CrossSectionShape.EGG,
                ]
            )
        )
        result = list(closed_definitions.with_session(session).all())

        # tabulated cross-section definitions are closed when the last element of 'width'
        # is zero
        tabulated_definitions = definitions_in_use.filter(
            models.CrossSectionDefinition.shape.in_(
                [
                    constants.CrossSectionShape.TABULATED_RECTANGLE,
                    constants.CrossSectionShape.TABULATED_TRAPEZIUM,
                ]
            )
        )
        for definition in tabulated_definitions.with_session(session).all():
            try:
                if float(definition.width.split(" ")[-1]) == 0.0:
                    # Closed channel
                    result.append(definition)
            except Exception:
                # Many things can go wrong, these are caught elsewhere
                pass
        return result

    def description(self) -> str:
        return (
            f"{self.column} has a closed cross section definition while "
            f"NumericalSettings.use_of_nested_newton is switched off. "
            f"This gives convergence issues. We recommend setting use_of_nested_newton = 1."
        )


class BoundaryCondition1DObjectNumberCheck(BaseCheck):
    """Check that the number of connected objects to 1D boundary connections is 1."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            column=models.BoundaryCondition1D.connection_node_id, *args, **kwargs
        )

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalid_ids = []
        for bc in self.to_check(session).all():
            total_objects = 0
            for table in [
                models.Channel,
                models.Pipe,
                models.Culvert,
                models.Orifice,
                models.Weir,
            ]:
                total_objects += (
                    session.query(table)
                    .filter(table.connection_node_start_id == bc.connection_node_id)
                    .count()
                )
                total_objects += (
                    session.query(table)
                    .filter(table.connection_node_end_id == bc.connection_node_id)
                    .count()
                )
            if total_objects != 1:
                invalid_ids.append(bc.id)

        return self.to_check(session).filter(
            models.BoundaryCondition1D.id.in_(invalid_ids)
        )

    def description(self) -> str:
        return "1D boundary condition should be connected to exactly one object."
