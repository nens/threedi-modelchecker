from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, NamedTuple

from sqlalchemy import and_, case, cast, distinct, func, not_, REAL, select, text
from sqlalchemy.orm import aliased, Query, Session
from threedi_schema.domain import constants, models

from .base import BaseCheck, CheckLevel
from .cross_section_definitions import cross_section_configuration
from .geo_query import distance, length, transform

# Use these to make checks only work on the first global settings entry:
first_setting = (
    Query(models.GlobalSetting.id)
    .order_by(models.GlobalSetting.id)
    .limit(1)
    .scalar_subquery()
)
first_setting_filter = models.GlobalSetting.id == first_setting


class CorrectAggregationSettingsExist(BaseCheck):
    """Check if aggregation settings are correctly filled with aggregation_method and flow_variable as required"""

    def __init__(
        self,
        aggregation_method: constants.AggregationMethod,
        flow_variable: constants.FlowVariable,
        *args,
        **kwargs,
    ):
        super().__init__(column=models.GlobalSetting.id, *args, **kwargs)
        self.aggregation_method = aggregation_method.value
        self.flow_variable = flow_variable.value

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        global_settings = self.to_check(session).filter(first_setting_filter)
        correctly_defined = session.execute(
            select(models.AggregationSettings)
            .filter(
                models.AggregationSettings.aggregation_method
                == self.aggregation_method,
                models.AggregationSettings.flow_variable == self.flow_variable,
            )
            .filter(
                models.AggregationSettings.global_settings_id
                == global_settings.subquery().c.id
            )
        ).all()

        return global_settings.all() if len(correctly_defined) == 0 else []

    def description(self) -> str:
        return (
            "To use the water balance tool, v2_aggregation_settings should have a row where "
            f"aggregation_method is {self.aggregation_method} and flow_variable is {self.flow_variable}."
        )


class CrossSectionLocationCheck(BaseCheck):
    """Check if cross section locations are within {max_distance} of their channel."""

    def __init__(self, max_distance, *args, **kwargs):
        super().__init__(column=models.CrossSectionLocation.the_geom, *args, **kwargs)
        self.max_distance = max_distance

    def get_invalid(self, session):
        # get all channels with more than 1 cross section location
        return (
            self.to_check(session)
            .join(models.Channel)
            .filter(
                distance(models.CrossSectionLocation.the_geom, models.Channel.the_geom)
                > self.max_distance
            )
            .all()
        )

    def description(self):
        return (
            f"v2_cross_section_location.the_geom is invalid: the cross-section location "
            f"should be located on the channel geometry (tolerance = {self.max_distance} m)"
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
        # get all channels with more than 1 cross section location
        cross_sections = (
            select(
                models.CrossSectionLocation.id.label("cross_section_id"),
                models.CrossSectionLocation.channel_id,
                models.CrossSectionDefinition.shape,
                models.CrossSectionDefinition.width,
                models.CrossSectionDefinition.height,
                self.first_number_in_spaced_string(
                    models.CrossSectionDefinition.width
                ).label("first_width"),
                self.first_number_in_spaced_string(
                    models.CrossSectionDefinition.height
                ).label("first_height"),
                self.last_number_in_spaced_string(
                    models.CrossSectionDefinition.width
                ).label("last_width"),
                self.last_number_in_spaced_string(
                    models.CrossSectionDefinition.height
                ).label("last_height"),
            )
            .select_from(models.CrossSectionLocation)
            .join(
                models.CrossSectionDefinition,
                models.CrossSectionLocation.definition_id
                == models.CrossSectionDefinition.id,
            )
            .subquery()
        )
        cross_sections_with_configuration = select(
            cross_sections.c.cross_section_id,
            cross_sections.c.shape,
            cross_sections.c.last_width,
            cross_sections.c.channel_id,
            self.configuration_type(
                shape=cross_sections.c.shape,
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

        def is_valid_series(input):
            try:
                [float(i) for i in input.split(" ")]
                return True
            except ValueError:
                return False

        def is_valid_value(input):
            if input in ["", None] or is_valid_series(input):
                return True
            else:
                return False

        all_cross_sections = session.execute(
            select(
                models.CrossSectionDefinition.width,
                models.CrossSectionDefinition.height,
            )
        )

        error_in_cross_sections = False

        for row in all_cross_sections.all():
            if not is_valid_value(row[0]) or not is_valid_value(row[1]):
                error_in_cross_sections = True
                break  # no need to continue checking; one error is enough to not run the check

        # only run the check if all the cross-section definitions have a parsable width and height
        # otherwise sqlalchemy will throw an exception
        # this is also checked in checks 87 and 88 (CrossSectionFloatListCheck), where it gives an error to the user
        if not error_in_cross_sections:
            return (
                self.to_check(session)
                .filter(self.column == filtered_cross_sections.c.channel_id)
                .all()
            )
        else:
            return []

    def description(self):
        return f"{self.column_name} has both open and closed cross-sections along its length. All cross-sections on a {self.column_name} object must be either open or closed."


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
            f"When {self.column_name} is used, there should exist at least one "
            "(impervious) surface."
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
    GlobalSettings.epsg_code.
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
            .join(start_node, self.start_node)
            .join(end_node, self.end_node)
            .filter(
                distance(start_node.the_geom, end_node.the_geom) < self.min_distance
            )
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
            .execute(query, {"min_distance": self.minimum_distance})
            .fetchall()
        )

        return results

    def description(self) -> str:
        return (
            f"The connection_node is within {self.minimum_distance} degrees of "
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
            connection_node_id_col = models.Channel.connection_node_start_id
        else:
            func_agg = func.MAX
            connection_node_id_col = models.Channel.connection_node_end_id

        channels_with_cs_locations = (
            session.query(
                models.Channel.id,
                models.CrossSectionLocation,
                func_agg(
                    func.Line_Locate_Point(
                        models.Channel.the_geom, models.CrossSectionLocation.the_geom
                    )
                ),
            )
            .join(models.Channel, isouter=True)
            .group_by(models.Channel.id)
        )
        channels_with_manholes = channels_with_cs_locations.join(
            models.Manhole,
            connection_node_id_col == models.Manhole.connection_node_id,
        )
        channels_manholes_level_checked = channels_with_manholes.having(
            models.CrossSectionLocation.reference_level < models.Manhole.bottom_level
        )

        return channels_manholes_level_checked.all()

    def description(self) -> str:
        return (
            f"The v2_manhole.bottom_level at the {self.nodes_to_check} of this v2_channel is higher than the "
            "v2_cross_section_location.reference_level closest to the manhole. This will be "
            "automatically fixed in threedigrid-builder."
        )


class OpenChannelsWithNestedNewton(BaseCheck):
    """Checks whether the model has any closed cross-section in use when the
    NumericalSettings.use_of_nested_newton is turned off.

    See https://github.com/nens/threeditoolbox/issues/522
    """

    def __init__(self, level=CheckLevel.WARNING, *args, **kwargs):
        super().__init__(
            column=models.CrossSectionDefinition.id,
            level=level,
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
            f"{self.column_name} has a closed cross section definition while "
            f"NumericalSettings.use_of_nested_newton is switched off. "
            f"This gives convergence issues. We recommend setting use_of_nested_newton = 1."
        )


class LinestringLocationCheck(BaseCheck):
    """Check that linestring geometry starts / ends are close to their connection nodes

    This allows for reversing the geometries. threedi-gridbuilder will reverse the geometries if
    that lowers the distance to the connection nodes.
    """

    def __init__(self, *args, **kwargs):
        self.max_distance = kwargs.pop("max_distance")
        super().__init__(*args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        start_node = aliased(models.ConnectionNode)
        end_node = aliased(models.ConnectionNode)

        tol = self.max_distance
        start_point = func.ST_PointN(self.column, 1)
        end_point = func.ST_PointN(self.column, func.ST_NPoints(self.column))

        start_ok = distance(start_point, start_node.the_geom) <= tol
        end_ok = distance(end_point, end_node.the_geom) <= tol
        start_ok_if_reversed = distance(end_point, start_node.the_geom) <= tol
        end_ok_if_reversed = distance(start_point, end_node.the_geom) <= tol
        return (
            self.to_check(session)
            .join(start_node, start_node.id == self.table.c.connection_node_start_id)
            .join(end_node, end_node.id == self.table.c.connection_node_end_id)
            .filter(
                ~(start_ok & end_ok),
                ~(start_ok_if_reversed & end_ok_if_reversed),
            )
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} does not start or end at its connection node (tolerance = {self.max_distance} m)"


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
            func.CheckSpatialIndex(self.column.table.name, self.column.name)
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
        linestring = models.Channel.the_geom
        tol = self.min_distance
        breach_point = func.Line_Locate_Point(
            transform(linestring), transform(func.ST_PointN(self.column, 1))
        )
        dist_1 = breach_point * length(linestring)
        dist_2 = (1 - breach_point) * length(linestring)
        return (
            self.to_check(session)
            .join(models.Channel)
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
            breach_point = func.Line_Locate_Point(
                transform(linestring), transform(func.ST_PointN(point, 1))
            )
            return (breach_point * length(linestring)).label("position")

        potential_breaches = sorted(
            session.query(
                self.table, get_position(self.column, models.Channel.the_geom)
            )
            .join(models.Channel)
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
            session.query(models.Pumpstation)
            .join(
                models.ConnectionNode,
                models.Pumpstation.connection_node_start_id == models.ConnectionNode.id,
            )
            .filter(
                (models.ConnectionNode.storage_area != None)
                & (
                    (  # calculate how many seconds the pumpstation takes to empty its storage: (storage * height)/pump capacity
                        (
                            # Arithmetic operations on None return None, so without this
                            # conditional type cast, no invalid results would be returned
                            # even if the storage_area was set to None.
                            models.ConnectionNode.storage_area
                            * (
                                models.Pumpstation.start_level
                                - models.Pumpstation.lower_stop_level
                            )
                        )
                    )
                    / (models.Pumpstation.capacity / 1000)
                    < Query(models.GlobalSetting.sim_time_step)
                    .filter(first_setting_filter)
                    .scalar_subquery()
                )
            )
            .all()
        )

    def description(self) -> str:
        return f"{self.column_name} will empty its storage faster than one timestep, which can cause simulation instabilities"


class ImperviousNodeInflowAreaCheck(BaseCheck):
    """Check that total inflow area per connection node is no larger than 10000 square metres"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        impervious_surfaces = (
            select(models.ImperviousSurfaceMap.connection_node_id)
            .select_from(models.ImperviousSurfaceMap)
            .join(
                models.ImperviousSurface,
                models.ImperviousSurfaceMap.impervious_surface_id
                == models.ImperviousSurface.id,
            )
            .group_by(models.ImperviousSurfaceMap.connection_node_id)
            .having(func.sum(models.ImperviousSurface.area) > 10000)
        ).subquery()

        return (
            session.query(models.ConnectionNode)
            .filter(
                models.ConnectionNode.id == impervious_surfaces.c.connection_node_id
            )
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

    def __init__(self, *args, surface_table, condition=True, **kwargs):
        super().__init__(*args, column=models.GlobalSetting.id, **kwargs)
        self.surface_table = surface_table
        self.condition = condition

    def get_invalid(self, session: Session):
        surface_table_length = session.execute(
            select(func.count(self.surface_table.id))
        ).scalar()
        return (
            session.query(models.GlobalSetting)
            .filter(self.condition, surface_table_length == 0)
            .all()
        )

    def description(self) -> str:
        return f"v2_global_settings.use_0d_inflow is set to use {self.surface_table.__tablename__}, but {self.surface_table.__tablename__} does not contain any features."


class NodeSurfaceConnectionsCheck(BaseCheck):
    """Check that no more than 50 surfaces are mapped to a connection node"""

    def __init__(
        self,
        check_type: Literal["impervious", "pervious"] = "impervious",
        *args,
        **kwargs,
    ):
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)

        self.surface_column = None
        if check_type == "impervious":
            self.surface_column = models.ImperviousSurfaceMap
        elif check_type == "pervious":
            self.surface_column = models.SurfaceMap

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        if self.surface_column is None:
            return []

        overloaded_connections = (
            select(self.surface_column.connection_node_id)
            .group_by(self.surface_column.connection_node_id)
            .having(func.count(self.surface_column.connection_node_id) > 50)
        ).subquery()

        return (
            session.query(models.ConnectionNode)
            .filter(
                models.ConnectionNode.id == overloaded_connections.c.connection_node_id
            )
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
        for record in session.execute(
            select(
                self.table.c.id,
                self.table.c.cross_section_definition_id,
                models.CrossSectionDefinition.shape,
                models.CrossSectionDefinition.width,
                models.CrossSectionDefinition.height,
            )
            .join(
                models.CrossSectionDefinition,
                self.table.c.cross_section_definition_id
                == models.CrossSectionDefinition.id,
                isouter=True,
            )
            .where(
                (models.CrossSectionDefinition.width != None)
                & (models.CrossSectionDefinition.width != "")
            )
        ):
            try:
                widths = [float(x) for x in record.width.split(" ")]
                heights = (
                    [float(x) for x in record.height.split(" ")]
                    if record.height not in [None, ""]
                    else []
                )
            except ValueError:
                continue  # other check catches this

            _, _, configuration = cross_section_configuration(
                shape=record.shape.value, heights=heights, widths=widths
            )

            # Pipes and culverts should generally have a closed cross-section
            if configuration == "open":
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} has an open cross-section, which is unusual for this feature. Please make sure this is not a mistake."


class DefinedAreaCheck(BaseCheck):
    """Check if the value in the 'area' column matches the surface area of 'the_geom'"""

    def __init__(self, *args, max_difference=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_difference = max_difference

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        all_results = select(
            self.table.c.id,
            self.table.c.area,
            self.table.c.the_geom,
            func.ST_Area(transform(self.table.c.the_geom)).label("calculated_area"),
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


class AllPresent(BaseCheck, ABC):
    """Base class to check if all or none values are present for a list of columns"""

    def __init__(self, columns, *args, **kwargs):
        self.columns = columns
        super().__init__(*args, **kwargs)

    @abstractmethod
    def _get_records(self, session):
        pass

    def get_invalid(self, session):
        # Create filters that find all rows where all or none of the values are present
        filter_condition_all = and_(
            *[(col != None) & (col != "") for col in self.columns]
        )
        filter_condition_none = and_(
            *[(col == None) | (col == "") for col in self.columns]
        )
        # Return all rows where neither all or none values are present
        return (
            self._get_records(session)
            .filter(not_(filter_condition_all))
            .filter(not_(filter_condition_none))
            .all()
        )

    def description(self):
        column_string = ",".join(
            [f"{column.table.name}.{column.name}" for column in self.columns]
        )
        return f"All of these columns must be defined: {column_string}"


class AllPresentFixedVegetationParameters(AllPresent):
    """Check if all or none vegetation values are defined in the CrossSectionLocation table"""

    def __init__(self, *args, **kwargs):
        columns = [
            models.CrossSectionLocation.vegetation_drag_coefficient,
            models.CrossSectionLocation.vegetation_height,
            models.CrossSectionLocation.vegetation_stem_diameter,
            models.CrossSectionLocation.vegetation_stem_density,
        ]
        super().__init__(columns, *args, **kwargs)

    def _get_records(self, session):
        # Get records with valid settings for vegetation in CrossSectionLocation
        return (
            session.query(models.CrossSectionLocation)
            .join(
                models.CrossSectionDefinition,
                models.CrossSectionDefinition.id
                == models.CrossSectionLocation.definition_id,
            )
            .filter(
                models.CrossSectionLocation.friction_type.is_(
                    constants.FrictionType.CHEZY
                )
            )
            .filter(
                models.CrossSectionDefinition.shape.is_(
                    constants.CrossSectionShape.TABULATED_YZ
                )
            )
        )


class AllPresentVariableVegetationParameters(AllPresent):
    def __init__(self, *args, **kwargs):
        columns = [
            models.CrossSectionDefinition.vegetation_drag_coefficients,
            models.CrossSectionDefinition.vegetation_heights,
            models.CrossSectionDefinition.vegetation_stem_diameters,
            models.CrossSectionDefinition.vegetation_stem_densities,
        ]
        super().__init__(columns, *args, **kwargs)

    def _get_records(self, session):
        # Get records with valid settings for vegetation in CrossSectionDefinition
        return (
            session.query(models.CrossSectionDefinition)
            .join(
                models.CrossSectionLocation,
                models.CrossSectionDefinition.id
                == models.CrossSectionLocation.definition_id,
            )
            .filter(
                models.CrossSectionLocation.friction_type.is_(
                    constants.FrictionType.CHEZY_CONVEYANCE
                )
            )
            .filter(
                models.CrossSectionDefinition.shape.is_(
                    constants.CrossSectionShape.TABULATED_YZ
                )
            )
        )
