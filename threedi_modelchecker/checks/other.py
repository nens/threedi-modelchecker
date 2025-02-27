import re
from dataclasses import dataclass
from typing import List, Literal, NamedTuple

import pyproj
from geoalchemy2.functions import ST_Distance, ST_Length
from sqlalchemy import (
    and_,
    case,
    cast,
    distinct,
    func,
    not_,
    REAL,
    select,
    text,
    union_all,
)
from sqlalchemy.orm import aliased, Query, Session
from threedi_schema.domain import constants, models

from .base import BaseCheck, CheckLevel
from .cross_section_definitions import cross_section_configuration_for_record


class CorrectAggregationSettingsExist(BaseCheck):
    """Check if aggregation settings are correctly filled with aggregation_method and flow_variable as required"""

    def __init__(
        self,
        aggregation_method: constants.AggregationMethod,
        flow_variable: constants.FlowVariable,
        *args,
        **kwargs,
    ):
        super().__init__(column=models.ModelSettings.id, *args, **kwargs)
        self.aggregation_method = aggregation_method.value
        self.flow_variable = flow_variable.value

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        global_settings = self.to_check(session)
        correctly_defined = session.execute(
            select(models.AggregationSettings).filter(
                models.AggregationSettings.aggregation_method
                == self.aggregation_method,
                models.AggregationSettings.flow_variable == self.flow_variable,
            )
        ).all()
        return global_settings.all() if len(correctly_defined) == 0 else []

    def description(self) -> str:
        return (
            "To use the water balance tool, aggregation_settings should have a row where "
            f"aggregation_method is {self.aggregation_method} and flow_variable is {self.flow_variable}."
        )


class CrossSectionSameConfigurationCheck(BaseCheck):
    """Check the cross-sections on the object are either all open or all closed."""

    def first_number_in_spaced_string(self, spaced_string):
        """return the first number in a space-separated string like '1 2 3'"""
        return cast(
            func.substr(
                spaced_string,
                1,
                func.instr(spaced_string, " ") - 1,
            ),
            REAL,
        )

    def last_number_in_spaced_string(self, spaced_string):
        """return the last number in a space-separated string like '1 2 3'"""
        return cast(
            func.replace(
                spaced_string,
                func.rtrim(
                    spaced_string,
                    func.replace(spaced_string, " ", ""),
                ),
                "",
            ),
            REAL,
        )

    def get_first_in_str(self, col, sep):
        return func.substr(
            col,
            1,
            func.instr(col, sep) - 1,
        )

    def get_last_in_str(self, col, sep):
        return func.replace(
            col,
            func.rtrim(
                col,
                func.replace(col, sep, ""),
            ),
            "",
        )

    def first_row_width(self):
        first_row = self.get_first_in_str(
            models.CrossSectionLocation.cross_section_table, "\n"
        )
        return cast(self.get_first_in_str(first_row, ","), REAL)

    def first_row_height(self):
        first_row = self.get_first_in_str(
            models.CrossSectionLocation.cross_section_table, "\n"
        )
        return cast(self.get_last_in_str(first_row, ","), REAL)

    def last_row_width(self):
        last_row = self.get_last_in_str(
            models.CrossSectionLocation.cross_section_table, "\n"
        )
        return cast(self.get_first_in_str(last_row, ","), REAL)

    def last_row_height(self):
        last_row = self.get_last_in_str(
            models.CrossSectionLocation.cross_section_table, "\n"
        )
        return cast(self.get_last_in_str(last_row, ","), REAL)

    def configuration_type(
        self, shape, first_width, last_width, first_height, last_height
    ):
        return case(
            (
                (
                    (shape.in_([0, 2, 3, 8]))
                    | (shape.in_([5, 6]) & (last_width == 0))
                    | (
                        (shape == 7)
                        & (first_width == last_width)
                        & (first_height == last_height)
                    )
                ),
                "closed",
            ),
            (
                (
                    (shape == 1)
                    | ((shape.in_([5, 6]) & (last_width > 0)))
                    | (
                        (shape == 7)
                        & ((first_width != last_width) | (first_height != last_height))
                    )
                ),
                "open",
            ),
            else_="open",
        )

    def get_invalid(self, session):
        # find all tabulated cross sections
        cross_sections_tab = select(
            models.CrossSectionLocation.id.label("cross_section_id"),
            models.CrossSectionLocation.channel_id,
            models.CrossSectionLocation.cross_section_shape,
            models.CrossSectionLocation.cross_section_table,
            self.first_row_width().label("first_width"),
            self.first_row_height().label("first_height"),
            self.last_row_width().label("last_width"),
            self.last_row_height().label("last_height"),
        ).where(models.CrossSectionLocation.cross_section_shape.in_([5, 6, 7]))
        # find all non tabulated cross sections
        cross_sections_notab = select(
            models.CrossSectionLocation.id.label("cross_section_id"),
            models.CrossSectionLocation.channel_id,
            models.CrossSectionLocation.cross_section_shape,
            models.CrossSectionLocation.cross_section_table,
            models.CrossSectionLocation.cross_section_width.label("first_width"),
            models.CrossSectionLocation.cross_section_height.label("first_height"),
            models.CrossSectionLocation.cross_section_width.label("last_width"),
            models.CrossSectionLocation.cross_section_height.label("last_height"),
        ).where(~models.CrossSectionLocation.cross_section_shape.in_([5, 6, 7]))
        # combine the above two queries to get all cross sections
        cross_sections = union_all(cross_sections_tab, cross_sections_notab).subquery()
        cross_sections_with_configuration = select(
            cross_sections.c.cross_section_id,
            cross_sections.c.cross_section_shape,
            cross_sections.c.last_width,
            cross_sections.c.channel_id,
            self.configuration_type(
                shape=cross_sections.c.cross_section_shape,
                first_width=cross_sections.c.first_width,
                last_width=cross_sections.c.last_width,
                first_height=cross_sections.c.first_height,
                last_height=cross_sections.c.last_height,
            ).label("configuration"),
        ).subquery()

        filtered_cross_sections = (
            select(cross_sections_with_configuration)
            .group_by(cross_sections_with_configuration.c.channel_id)
            .having(
                func.count(distinct(cross_sections_with_configuration.c.configuration))
                > 1
            )
            .subquery()
        )
        return (
            self.to_check(session)
            .filter(self.column == filtered_cross_sections.c.channel_id)
            .all()
        )

    def description(self):
        return f"{self.column_name} has both open and closed cross-sections along its length. All cross-sections on a {self.column_name} object must be either open or closed."


class Use0DFlowCheck(BaseCheck):
    """Check that when use_0d_flow in global settings is configured to 1 or to
    2, there is at least one impervious surface or surfaces respectively.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            column=models.SimulationTemplateSettings.use_0d_inflow, *args, **kwargs
        )

    def get_invalid(self, session):
        settings = session.query(models.SimulationTemplateSettings).one_or_none()
        if settings is None:
            return []
        use_0d_flow = settings.use_0d_inflow
        if use_0d_flow != constants.InflowType.NO_INFLOW:
            surface_count = session.query(func.count(models.Surface.id)).scalar()
            if surface_count == 0:
                return [settings]
        return []

    def description(self):
        return (
            f"When {self.column_name} is used, there should exist at least one surface."
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
    `min_distance`.
    """

    def __init__(
        self,
        start_node,
        end_node,
        min_distance: float,
        recommended_distance: float = 1.0,
        *args,
        **kwargs,
    ):
        """

        :param start_node: column name of the start node
        :param end_node: column name of the end node
        :param min_distance: minimum required distance between start and end node
        """
        super().__init__(*args, **kwargs)
        self.start_node = start_node
        self.end_node = end_node
        self.min_distance = min_distance
        self.recommended_distance = recommended_distance

    def get_invalid(self, session):
        start_node = aliased(models.ConnectionNode)
        end_node = aliased(models.ConnectionNode)
        q = (
            self.to_check(session)
            .join(start_node, start_node.id == self.start_node)
            .join(end_node, end_node.id == self.end_node)
            .filter(ST_Distance(start_node.geom, end_node.geom) < self.min_distance)
        )
        return list(q.with_session(session).all())

    def description(self) -> str:
        return (
            f"The length of {self.table} is "
            f"very short (< {self.min_distance}). A length of at least {self.recommended_distance} m is recommended to avoid timestep reduction."
        )


class ConnectionNodesDistance(BaseCheck):
    """Check that the distance between connection nodes is above a certain
    threshold
    """

    def __init__(
        self, minimum_distance: float, level=CheckLevel.WARNING, *args, **kwargs
    ):
        """
        :param minimum_distance: threshold distance in degrees
        """
        super().__init__(column=models.ConnectionNode.id, level=level, *args, **kwargs)
        self.minimum_distance = minimum_distance

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        """
        The query makes use of the SpatialIndex so we won't have to calculate the
        distance between all connection nodes.
        """
        query = text(
            f"""
            SELECT *
            FROM connection_node AS cn1, connection_node AS cn2
            WHERE ST_Distance(cn1.geom, cn2.geom) < {self.minimum_distance}
            AND cn1.ROWID != cn2.ROWID
            AND cn2.ROWID IN (
                SELECT ROWID
                FROM rtree_connection_node_geom
                WHERE (
                    maxx >= ST_MinX(ST_Buffer(cn1.geom, {self.minimum_distance / 2}))
                    AND minx <= ST_MaxX(ST_Buffer(cn1.geom, {self.minimum_distance / 2}))
                    AND maxy >= ST_MinY(ST_Buffer(cn1.geom, {self.minimum_distance / 2}))
                    AND miny <= ST_MaxY(ST_Buffer(cn1.geom, {self.minimum_distance / 2}))
                )
            )
            """
        )
        results = session.connection().execute(query).fetchall()
        return results

    def description(self) -> str:

        return (
            f"The connection_node is within {self.minimum_distance * 100} cm of "
            f"another connection_node."
        )


class ChannelManholeLevelCheck(BaseCheck):
    """Check that the reference_level of a channel is higher than or equal to the bottom_level of a manhole
    connected to the channel as measured at the cross-section closest to the manhole. This check runs if the
    manhole is on the channel's starting node.
    """

    def __init__(
        self,
        level: CheckLevel = CheckLevel.INFO,
        nodes_to_check: Literal["start", "end"] = "start",
        *args,
        **kwargs,
    ):
        """
        :param level: severity of the check, defaults to CheckLevel.INFO. Options are
        in checks.base.CheckLevel
        :param nodes_to_check: whether to check for manholes at the start of the channel
        or at the end of the channel. Options are "start" and "end", defaults to "start"
        """
        if nodes_to_check not in ["start", "end"]:
            raise ValueError("nodes_to_check must be 'start' or 'end'")
        super().__init__(column=models.Channel.id, level=level, *args, **kwargs)
        self.nodes_to_check = nodes_to_check

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        """
        This query does the following:
        channel_with_cs_locations       : left join between cross_sections and channels, to get a table containing
                                          all cross-sections and the channels they lie on
        channels_with_manholes          : join between channel_with_cs_locations and manholes, to get all channels with
                                          a manhole on the channel's start node if self.nodes_to_check == "start", or all
                                          channels with a manhole on the channel's end node if self.nodes_to_check == "start".
        channels_manholes_level_checked : filter the query on invalid entries; that is, entries where the cross-section
                                          reference level is indeed lower than the manhole bottom level. having is used instead
                                          of filter because the query being filtered is a aggregate produced by groupby.
        """
        if self.nodes_to_check == "start":
            func_agg = func.MIN
            connection_node_id_col = models.Channel.connection_node_id_start
        else:
            func_agg = func.MAX
            connection_node_id_col = models.Channel.connection_node_id_end

        channels_with_cs_locations = (
            session.query(
                models.Channel.id,
                models.CrossSectionLocation,
                func_agg(
                    func.Line_Locate_Point(
                        models.Channel.geom, models.CrossSectionLocation.geom
                    )
                ),
            )
            .join(
                models.CrossSectionLocation,
                models.CrossSectionLocation.channel_id == models.Channel.id,
            )
            .group_by(models.Channel.id)
        )

        channels_with_manholes = channels_with_cs_locations.join(
            models.ConnectionNode, models.ConnectionNode.id == connection_node_id_col
        )

        channels_manholes_level_checked = channels_with_manholes.having(
            models.CrossSectionLocation.reference_level
            < models.ConnectionNode.bottom_level
        )

        return channels_manholes_level_checked.all()

    def description(self) -> str:
        return (
            f"The connection_node.bottom_level at the {self.nodes_to_check} of this channel is higher than the "
            "cross_section_location.reference_level closest to the connection-node. This will be "
            "automatically fixed in threedigrid-builder."
        )


class OpenChannelsWithNestedNewton(BaseCheck):
    """Checks whether the model has any closed cross-section in use when the
    NumericalSettings.use_nested_newton is turned off.

    See https://github.com/nens/threeditoolbox/issues/522
    """

    def __init__(self, column, level=CheckLevel.WARNING, *args, **kwargs):
        super().__init__(
            # column=table.id,
            column=column,
            level=level,
            filters=Query(models.NumericalSettings)
            .filter(models.NumericalSettings.use_nested_newton == 0)
            .exists(),
            *args,
            **kwargs,
        )
        # self.table = table

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalids = []
        for record in self.to_check(session):
            _, _, configuration = cross_section_configuration_for_record(record)

            if configuration == "closed":
                invalids.append(record)
        return invalids

    def description(self) -> str:
        return (
            f"{self.column_name} has a closed cross section definition while "
            f"NumericalSettings.use_nested_newton is switched off. "
            f"This gives convergence issues. We recommend setting use_nested_newton = 1."
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
                    .filter(table.connection_node_id_start == bc.connection_node_id)
                    .count()
                )
                total_objects += (
                    session.query(table)
                    .filter(table.connection_node_id_end == bc.connection_node_id)
                    .count()
                )
            if total_objects != 1:
                invalid_ids.append(bc.id)

        return (
            self.to_check(session)
            .filter(models.BoundaryCondition1D.id.in_(invalid_ids))
            .all()
        )

    def description(self) -> str:
        return "1D boundary condition should be connected to exactly one object."


@dataclass
class IndexMissingRecord:
    id: int
    table_name: str
    column_name: str


class SpatialIndexCheck(BaseCheck):
    """Checks whether a spatial index is present and valid"""

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        result = session.execute(
            text(
                f"""
            SELECT EXISTS(
                SELECT 1 FROM sqlite_master
                WHERE type='table'
                AND name='rtree_{self.column.table.name}_{self.column.name}'
            );
        """
            )
        ).scalar()
        if result == 1:
            return []
        else:
            return [
                IndexMissingRecord(
                    id=1,
                    table_name=self.column.table.name,
                    column_name=self.column.name,
                )
            ]

    def description(self) -> str:
        return f"{self.column_name} has no valid spatial index, which is required for some checks"


class PotentialBreachStartEndCheck(BaseCheck):
    """Check that a potential breach is exactly on or >=1 m from a linestring start/end."""

    def __init__(self, *args, **kwargs):
        self.min_distance = kwargs.pop("min_distance")

        super().__init__(*args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        linestring = models.Channel.geom
        tol = self.min_distance
        breach_point = func.Line_Locate_Point(
            linestring, func.ST_PointN(self.column, 1)
        )
        dist_1 = breach_point * ST_Length(linestring)
        dist_2 = (1 - breach_point) * ST_Length(linestring)
        return (
            self.to_check(session)
            .join(models.Channel, self.table.c.channel_id == models.Channel.id)
            .filter(((dist_1 > 0) & (dist_1 < tol)) | ((dist_2 > 0) & (dist_2 < tol)))
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} must be exactly on or >= {self.min_distance} m from a start or end channel vertex"


class PotentialBreachInterdistanceCheck(BaseCheck):
    """Check that a potential breaches are exactly on the same place or >=1 m apart."""

    def __init__(self, *args, **kwargs):
        self.min_distance = kwargs.pop("min_distance")
        assert "filters" not in kwargs

        super().__init__(*args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        # this query is hard to get performant; we do a hybrid sql / Python approach

        # First fetch the position of each potential breach per channel
        def get_position(point, linestring):
            breach_point = func.Line_Locate_Point(linestring, func.ST_PointN(point, 1))
            return (breach_point * ST_Length(linestring)).label("position")

        potential_breaches = sorted(
            session.query(self.table, get_position(self.column, models.Channel.geom))
            .join(models.Channel, self.table.c.channel_id == models.Channel.id)
            .all(),
            key=lambda x: (x.channel_id, x[-1]),
        )

        invalid = []
        prev_channel_id = -9999
        prev_position = -1.0
        for breach in potential_breaches:
            if breach.channel_id != prev_channel_id:
                prev_channel_id, prev_position = breach.channel_id, breach.position
                continue
            if breach.position == prev_position:
                continue
            if (breach.position - prev_position) <= self.min_distance:
                invalid.append(breach)
        return invalid

    def description(self) -> str:
        return f"{self.column_name} must be more than {self.min_distance} m apart (or exactly on the same position)"


class PumpStorageTimestepCheck(BaseCheck):
    """Check that a pumpstation will not empty its storage area within one timestep"""

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        return (
            session.query(models.Pump)
            .join(
                models.ConnectionNode,
                models.Pump.connection_node_id == models.ConnectionNode.id,
            )
            .filter(
                (models.ConnectionNode.storage_area != None)
                & (
                    (
                        # calculate how many seconds the pumpstation takes to empty its storage: (storage * height)/pump capacity
                        (
                            # Arithmetic operations on None return None, so without this
                            # conditional type cast, no invalid results would be returned
                            # even if the storage_area was set to None.
                            models.ConnectionNode.storage_area
                            * (models.Pump.start_level - models.Pump.lower_stop_level)
                        )
                    )
                    / (models.Pump.capacity / 1000)
                    < Query(models.TimeStepSettings.time_step).scalar_subquery()
                )
            )
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} will empty its storage faster than one timestep, which can cause simulation instabilities"


class SurfaceNodeInflowAreaCheck(BaseCheck):
    """Check that total inflow area per connection node is no larger than 10000 square metres"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        surfaces = (
            select(models.SurfaceMap.connection_node_id)
            .select_from(models.SurfaceMap)
            .join(
                models.Surface,
                models.SurfaceMap.surface_id == models.Surface.id,
            )
            .group_by(models.SurfaceMap.connection_node_id)
            .having(func.sum(models.Surface.area) > 10000)
        ).subquery()

        return (
            session.query(models.ConnectionNode)
            .filter(models.ConnectionNode.id == surfaces.c.connection_node_id)
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} has a an associated inflow area larger than 10000 m2; this might be an error."


class PerviousNodeInflowAreaCheck(BaseCheck):
    """Check that total inflow area per connection node is no larger than 10000 square metres"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        pervious_surfaces = (
            select(models.SurfaceMap.connection_node_id)
            .select_from(models.SurfaceMap)
            .join(
                models.Surface,
                models.SurfaceMap.surface_id == models.Surface.id,
            )
            .group_by(models.SurfaceMap.connection_node_id)
            .having(func.sum(models.Surface.area) > 10000)
        ).subquery()

        return (
            session.query(models.ConnectionNode)
            .filter(models.ConnectionNode.id == pervious_surfaces.c.connection_node_id)
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} has a an associated inflow area larger than 10000 m2; this might be an error."


class InflowNoFeaturesCheck(BaseCheck):
    """Check that the surface table in the global use_0d_inflow setting contains at least 1 feature."""

    def __init__(self, *args, feature_table, condition=True, **kwargs):
        super().__init__(*args, column=models.ModelSettings.id, **kwargs)
        self.feature_table = feature_table
        self.condition = condition

    def get_invalid(self, session: Session):
        surface_table_length = session.execute(
            select(func.count(self.feature_table.id))
        ).scalar()
        return (
            session.query(models.ModelSettings)
            .filter(self.condition, surface_table_length == 0)
            .all()
        )

    def description(self) -> str:
        return f"model_settings.use_0d_inflow is set to use {self.feature_table.__tablename__}, but {self.feature_table.__tablename__} does not contain any features."


class NodeSurfaceConnectionsCheck(BaseCheck):
    """Check that no more than 50 surfaces are mapped to a connection node"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)
        self.surface_column = models.SurfaceMap

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        if self.surface_column is None:
            return []
        overloaded_connections = (
            select(models.SurfaceMap.connection_node_id)
            .group_by(models.SurfaceMap.connection_node_id)
            .having(func.count(models.SurfaceMap.connection_node_id) > 50)
        )

        return (
            self.to_check(session)
            .filter(models.ConnectionNode.id.in_(overloaded_connections))
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} has more than 50 surface areas mapped to it; this might be an error."


class FeatureClosedCrossSectionCheck(BaseCheck):
    """
    Check if feature has a closed cross-section
    """

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session):
            _, _, configuration = cross_section_configuration_for_record(record)

            # Pipes and culverts should generally have a closed cross-section
            if configuration == "open":
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} has an open cross-section, which is unusual for this feature. Please make sure this is not a mistake."


class DefinedAreaCheck(BaseCheck):
    """Check if the value in the 'area' column matches the surface area of 'geom'"""

    def __init__(self, *args, max_difference=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_difference = max_difference

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        all_results = select(
            self.table.c.id,
            self.table.c.area,
            self.table.c.geom,
            func.ST_Area(self.table.c.geom).label("calculated_area"),
        ).subquery()
        return (
            session.query(all_results)
            .filter(
                func.abs(all_results.c.area - all_results.c.calculated_area)
                > self.max_difference
            )
            .all()
        )

    def description(self):
        return f"{self.column_name} has a {self.column_name} (used in the simulation) differing from its geometrical area by more than 1 m2"


class BetaColumnsCheck(BaseCheck):
    """Check that no beta columns were used in the database"""

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        return session.query(self.table).filter(self.column.isnot(None)).all()

    def description(self) -> str:
        return f"{self.column_name} is a beta feature, which is still under development; please do not use it yet."


class BetaValuesCheck(BaseCheck):
    """Check that no beta features were used in the database"""

    def __init__(
        self,
        column,
        values: list = [],
        filters=None,
        level=CheckLevel.ERROR,
        error_code=0,
    ):
        super().__init__(column, filters, level, error_code)
        self.values = values

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        return session.query(self.table).filter(self.column.in_(self.values)).all()

    def description(self) -> str:
        return f"The value you have used for {self.column_name} is still in beta; please do not use it yet."


class AllPresentVegetationParameters(BaseCheck):
    """Check if all or none vegetation values are defined in the CrossSectionLocation table"""

    def __init__(self, *args, **kwargs):
        self.columns = [
            models.CrossSectionLocation.vegetation_drag_coefficient,
            models.CrossSectionLocation.vegetation_height,
            models.CrossSectionLocation.vegetation_stem_diameter,
            models.CrossSectionLocation.vegetation_stem_density,
        ]
        super().__init__(*args, **kwargs)

    def get_invalid(self, session):
        # Create filters that find all rows where all or none of the values are present
        filter_condition_all = and_(
            *[(col != None) & (col != "") for col in self.columns]
        )
        filter_condition_none = and_(
            *[(col == None) | (col == "") for col in self.columns]
        )
        # Return all rows where neither all or none values are present
        records = (
            session.query(models.CrossSectionLocation)
            .filter(
                models.CrossSectionLocation.friction_type.is_(
                    constants.FrictionType.CHEZY
                )
            )
            .filter(
                models.CrossSectionLocation.cross_section_shape.is_(
                    constants.CrossSectionShape.TABULATED_YZ
                )
            )
        )

        return (
            records.filter(not_(filter_condition_all))
            .filter(not_(filter_condition_none))
            .all()
        )


class UsedSettingsPresentCheck(BaseCheck):
    def __init__(
        self,
        column,
        settings_tables,
        filters=None,
        level=CheckLevel.ERROR,
        error_code=0,
    ):
        super().__init__(column, filters, level, error_code)
        self.settings_tables = settings_tables

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        # more than 1 row should be caught by another check
        all_results = self.to_check(session).filter(self.column == True).all()
        use_cols = len(all_results) > 0
        for table in self.settings_tables:
            if use_cols and session.query(table).count() == 0:
                return all_results
        return []

    def description(self) -> str:
        msg = f"{self.column_name} in {self.table.name} is set to True but "
        if len(self.settings_tables) == 1:
            msg += "{self.settings_tables[0].__tablename__} is empty"
        else:
            msg += (
                "["
                + ",".join(table.__tablename__ for table in self.settings_tables)
                + "] are empty"
            )
        return msg


class UsedSettingsPresentCheckSingleTable(UsedSettingsPresentCheck):
    def __init__(
        self,
        column,
        settings_table,
        filters=None,
        level=CheckLevel.ERROR,
        error_code=0,
    ):
        super().__init__(column, [settings_table], filters, level, error_code)


class MaxOneRecordCheck(BaseCheck):
    def __init__(self, column, filters=None, level=CheckLevel.ERROR, error_code=0):
        super().__init__(column, filters, level, error_code)
        self.observed_length = 0

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        # return mock list in case the table is empty when it shouldn't be
        all_results = self.to_check(session).all()
        self.observed_length = len(all_results)
        if self.observed_length > 1:
            return all_results if self.observed_length > 0 else ["foo"]
        else:
            return []

    def description(self) -> str:
        return (
            f"{self.table.name} has {self.observed_length} rows, "
            f"but should have at most 1 row."
        )


class TagsValidCheck(BaseCheck):
    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            query = (
                f"SELECT id FROM tags WHERE id IN ({getattr(record, self.column.name)})"
            )
            match_rows = session.connection().execute(text(query)).fetchall()
            found_idx = {row[0] for row in match_rows}
            req_idx = {int(x) for x in getattr(record, self.column.name).split(",")}
            if found_idx != req_idx:
                invalids.append(record)
        return invalids

    def description(self) -> str:
        return f"{self.table.name}.{self.column} refers to tag ids that are not present in Tags, "


class TableStrCheck(BaseCheck):
    def __init__(
        self, column, pattern, filters=None, level=CheckLevel.ERROR, error_code=0
    ):
        self.pattern = pattern
        super().__init__(
            column=column, filters=filters, level=level, error_code=error_code
        )

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        # return mock list in case the table is empty when it shouldn't be
        invalids = []
        for record in self.to_check(session).all():
            if re.match(self.pattern, getattr(record, self.column.name)) is None:
                invalids.append(record)
        return invalids


class TableControlActionTableCheckDefault(TableStrCheck):
    def __init__(self, level=CheckLevel.ERROR, error_code=0):
        # check for action_table for action_type != set_discharge_coefficients
        # expected format: multiple rows, separated by \n of "val,val"
        super().__init__(
            column=models.TableControl.action_table,
            pattern=r"^(-?\d+(\.\d+)?,-?\d+(\.\d+)?\n?)+$",
            filters=models.TableControl.action_type
            != constants.TableControlActionTypes.set_discharge_coefficients,
            level=level,
            error_code=error_code,
        )

        def description(self) -> str:
            return (
                f"{self.table.name}.{self.column} is not properly formatted."
                f"Expected one or more rows of: 'number, number number'"
            )


class TableControlActionTableCheckDischargeCoefficients(TableStrCheck):
    def __init__(self, level=CheckLevel.ERROR, error_code=0):
        # check for action_table for action_type = set_discharge_coefficients
        # expected format: multiple rows, separated by \n of "val,val val"
        super().__init__(
            column=models.TableControl.action_table,
            pattern=r"^(-?\d+(\.\d+)?,-?\d+(\.\d+)? -?\d+(\.\d+)?\n?)+$",
            filters=models.TableControl.action_type
            == constants.TableControlActionTypes.set_discharge_coefficients,
            level=level,
            error_code=error_code,
        )

    def description(self) -> str:
        return (
            f"{self.table.name}.{self.column} is not properly formatted."
            f"Expected one or more rows of: 'number, number'"
        )


class ControlHasSingleMeasureVariable(BaseCheck):
    def __init__(self, control_model, level=CheckLevel.ERROR, error_code=0):
        control_type_map = {
            models.TableControl: "table",
            models.MemoryControl: "memory",
        }
        self.control_type_name = control_type_map[control_model]
        super().__init__(
            column=control_model.id,
            level=level,
            error_code=error_code,
        )

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalid = []
        for record in self.to_check(session):
            res = (
                session.query(models.MeasureMap)
                .filter(
                    models.MeasureMap.control_type == self.control_type_name,
                    models.MeasureMap.control_id == record.id,
                )
                .join(
                    models.MeasureLocation,
                    models.MeasureMap.measure_location_id == models.MeasureLocation.id,
                )
                .with_entities(models.MeasureLocation.measure_variable)
            ).all()
            if len(res) == 0:
                continue
            first_measure_variable = res[0].measure_variable
            if not all(item[0] == first_measure_variable for item in res):
                invalid.append(record)
        return invalid

    def description(self) -> str:
        return f"{self.table.name} is mapped to measure locations with different measure variables"


class DWFDistributionBaseCheck(BaseCheck):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            column=models.DryWeatherFlowDistribution.distribution, *args, **kwargs
        )

    def get_distribution(self, record):
        str = getattr(record, self.column.name)
        return str.split(",")

    def get_distribution_values(self, record):
        return [float(x) for x in self.get_distribution(record)]


class DWFDistributionCSVFormatCheck(DWFDistributionBaseCheck):
    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                self.get_distribution_values(record)
            except ValueError:
                invalids.append(record)
        return invalids

    def description(self) -> str:
        return f"{self.table.name}.{self.column_name} should contain a list of comma-separated numbers"


class DWFDistributionLengthCheck(DWFDistributionBaseCheck):
    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            if len(self.get_distribution(record)) != 24:
                invalids.append(record)
        return invalids

    def description(self) -> str:
        return f"{self.table.name}.{self.column_name} should contain exactly 24 values"


class DWFDistributionSumCheck(DWFDistributionBaseCheck):
    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                values = self.get_distribution_values(record)
            except ValueError:
                # handled by DWFDistributionCSVFormatCheck
                continue
            if not (99.99 <= sum(values) <= 100.01):
                invalids.append(record)
        return invalids

    def description(self) -> str:
        return (
            f"The values in {self.table.name}.{self.column_name} should add up to 100 %"
        )


class ModelEPSGCheckValid(BaseCheck):
    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ModelSettings.id, *args, **kwargs)
        self.epsg_code = None

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        self.epsg_code = session.model_checker_context.epsg_ref_code
        if self.epsg_code is not None:
            try:
                pyproj.CRS.from_epsg(self.epsg_code)
            except pyproj.exceptions.CRSError:
                return self.to_check(session).all()
        return []

    def description(self) -> str:
        return f"Found invalid EPSG: {self.epsg_code}"


class ModelEPSGCheckProjected(BaseCheck):
    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ModelSettings.id, *args, **kwargs)
        self.epsg_code = None

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        self.epsg_code = session.model_checker_context.epsg_ref_code
        if self.epsg_code is not None:
            try:
                crs = pyproj.CRS.from_epsg(self.epsg_code)
            except pyproj.exceptions.CRSError:
                # handled by ModelEPSGCheckValid
                return []
            if not crs.is_projected:
                return self.to_check(session).all()
        return []

    def description(self) -> str:
        return f"EPSG {self.epsg_code} is not projected"


class ModelEPSGCheckUnits(BaseCheck):
    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ModelSettings.id, *args, **kwargs)
        self.epsg_code = None

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        self.epsg_code = session.model_checker_context.epsg_ref_code
        if self.epsg_code is not None:
            try:
                crs = pyproj.CRS.from_epsg(self.epsg_code)
            except pyproj.exceptions.CRSError:
                # handled by ModelEPSGCheckValid
                return []
            for ax in crs.axis_info:
                if not ax.unit_name == "metre":
                    return self.to_check(session).all()
        return []

    def description(self) -> str:
        return f"EPSG {self.epsg_code} is not fully defined in metres"
