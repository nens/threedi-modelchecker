from ..threedi_model import constants
from ..threedi_model import models
from .base import BaseCheck
from geoalchemy2 import functions as geo_func
from sqlalchemy import func
from sqlalchemy import or_
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

    def __init__(self):
        super().__init__(column=models.CrossSectionLocation.bank_level)

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
            "CrossSectionLoaction.Banklevel cannot be null when calculation_type "
            "is CONNECTED or DOUBLE_CONNECTED"
        )


class CrossSectionShapeCheck(BaseCheck):
    """Check if all CrossSectionDefinition.shape are valid"""

    def __init__(self):
        super().__init__(column=models.CrossSectionDefinition.shape)

    def get_invalid(self, session):
        cross_section_definitions = session.query(self.table)
        invalid_cross_section_shapes = []

        for cross_section_definition in cross_section_definitions.all():
            shape = cross_section_definition.shape
            width = cross_section_definition.width
            height = cross_section_definition.height
            if shape == constants.CrossSectionShape.RECTANGLE:
                if not valid_rectangle(width, height):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.CIRCLE:
                if not valid_circle(width):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.EGG:
                if not valid_egg(width):
                    invalid_cross_section_shapes.append(cross_section_definition)
            if shape == constants.CrossSectionShape.TABULATED_RECTANGLE:
                if not valid_tabulated_shape(width, height):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.TABULATED_TRAPEZIUM:
                if not valid_tabulated_shape(width, height):
                    invalid_cross_section_shapes.append(cross_section_definition)
        return invalid_cross_section_shapes

    def description(self):
        return "Invalid CrossSectionShape"


def valid_rectangle(width, height):
    if width is None:  # width is required
        return False
    width_match = patterns.POSITIVE_FLOAT_REGEX.fullmatch(width)
    if height is not None:  # height is not required
        height_match = patterns.POSITIVE_FLOAT_REGEX.fullmatch(height)
    else:
        height_match = True
    return width_match and height_match


def valid_circle(width):
    if width is None:
        return False
    return patterns.POSITIVE_FLOAT_REGEX.fullmatch(width)


def valid_egg(width):
    if width is None:
        return False
    try:
        w = float(width)
    except ValueError:
        return False
    return w > 0


def valid_tabulated_shape(width, height):
    """Return if the tabulated shape is valid.

    Validating that the strings `width` and `height` contain positive floats
    was previously done using a regex. However, experiments showed that
    trying to split the string and reading in the floats is much faster.

    :param width: string of widths
    :param height: string of heights
    :return: True if the shape if valid
    """
    if width is None or height is None:
        return False
    height_string_list = height.split(" ")
    width_string_list = width.split(" ")
    if len(height_string_list) != len(width_string_list):
        return False
    try:
        # first height must be 0
        first_height = float(height_string_list[0])
        if first_height != 0:
            return False
    except ValueError:
        return False
    previous_height = -1
    for h_string, w_string in zip(height_string_list, width_string_list):
        try:
            h = float(h_string)
            w = float(w_string)
        except ValueError:
            return False
        if h < 0:
            return False
        if w < 0:
            return False
        if h < previous_height:
            # height must be increasing
            return False
        previous_height = h
    return True


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
        return "Invalid timeseries"


class Use0DFlowCheck(BaseCheck):
    """Check that when use_0d_flow in global settings is configured to 1 or to
    2, there is at least one impervious surface or surfaces respectively.
    """

    def __init__(self):
        super().__init__(column=models.GlobalSetting.use_0d_inflow)

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
            if row.use_0d_inflow == 1 and impervious_surface_count == 0:
                invalid_rows.append(row)
            elif row.use_0d_inflow == 2 and surface_count == 0:
                invalid_rows.append(row)
            else:
                continue
        return invalid_rows

    def description(self):
        return (
            "When %s is used, there should exists at least one "
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

    def __init__(self):
        super().__init__(column=models.ConnectionNode.id)

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
        q = (
            Query(self.column.class_)
            .join(start_node, self.start_node)
            .join(end_node, self.end_node)
            .filter(
                geo_func.ST_Distance(
                    geo_func.ST_Transform(
                        start_node.the_geom,
                        Query(models.GlobalSetting.epsg_code)
                        .limit(1)
                        .label("epsg_code"),
                    ),
                    geo_func.ST_Transform(
                        end_node.the_geom,
                        Query(models.GlobalSetting.epsg_code)
                        .limit(1)
                        .label("epsg_code"),
                    ),
                )
                < self.min_distance
            )
        )
        return list(q.with_session(session).all())

    def description(self) -> str:
        return (
            f"The distance of start- and end connectionnode of {self.table} is "
            f"too short, should be at least {self.min_distance} meters"
        )


class ConnectionNodesDistance(BaseCheck):
    """Check that the distance between CONNECTED connection nodes is above a certain
    threshold
    """

    def __init__(self, minimum_distance: float, *args, **kwargs):
        """
        :param minimum_distance: threshold distance in meters
        """
        super().__init__(column=models.ConnectionNode.id, *args, **kwargs)
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
            """SELECT *
               FROM v2_connection_nodes AS cn1, v2_connection_nodes AS cn2
               WHERE
                   distance(cn1.the_geom, cn2.the_geom, 1) < :min_distance
                   AND cn1.ROWID != cn2.ROWID
                   AND cn2.ROWID IN (
                     SELECT ROWID
                     FROM SpatialIndex
                     WHERE (
                       f_table_name = "v2_connection_nodes"
                       AND search_frame = Buffer(cn1.the_geom, 0.0005)));
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
    """Checks whether the model has any open cross-section in use when the
    NumericalSettings.use_of_nested_newton is turned off.

    See https://github.com/nens/threeditoolbox/issues/522
    """

    def __init__(self):
        super().__init__(column=models.Channel.id)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        invalid_channels = []

        # Circle and egg cross-section definitions are always open:
        circle_egg_definitions = (
            Query(models.Channel)
            .join(models.CrossSectionLocation, models.Channel.cross_section_locations)
            .join(models.CrossSectionDefinition, models.CrossSectionLocation.definition)
            .filter(
                models.NumericalSettings.use_of_nested_newton == 0,
                or_(
                    models.CrossSectionDefinition.shape.in_(
                        [
                            constants.CrossSectionShape.CIRCLE,
                            constants.CrossSectionShape.EGG,
                        ]
                    )
                ),
            )
        )
        invalid_channels += circle_egg_definitions.with_session(session).all()

        # Tabulated cross-section definitions are open when the last element of 'width'
        # is zero
        open_definitions = (
            Query(
                [
                    models.Channel,
                    models.CrossSectionLocation,
                    models.CrossSectionDefinition,
                ]
            )
            .join(models.CrossSectionLocation, models.Channel.cross_section_locations)
            .join(models.CrossSectionDefinition, models.CrossSectionLocation.definition)
            .filter(
                models.NumericalSettings.use_of_nested_newton == 0,
                models.CrossSectionDefinition.shape.in_(
                    [
                        constants.CrossSectionShape.TABULATED_RECTANGLE,
                        constants.CrossSectionShape.TABULATED_TRAPEZIUM,
                    ]
                ),
            )
        )
        for channel, _, definition in open_definitions.with_session(session).all():
            try:
                if definition.width.split(" ")[-1] in ("0", "0.", "0.0"):
                    # Open channel
                    invalid_channels.append(channel)
            except Exception:
                # Many things can go wrong, I won't bother with trying to catch all
                # possible exceptions
                pass
        return invalid_channels

    def description(self) -> str:
        return (
            "Channel in the model with an open cross-section-definition while also "
            "having the NumericalSettings.use_of_nested_newton turned off can be a "
            "cause of instabilities in the simulation. Please turn on the "
            "NumericalSettings.use_of_nested_newton on or make the Channel a "
            "closed definition."
        )
