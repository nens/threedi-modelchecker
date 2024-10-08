from sqlalchemy import select
from threedi_schema import constants, models

from .base import BaseCheck

from enum import IntEnum

class TableColumn(IntEnum):
    width = 0
    height = 1
    both = 2


def parse_cross_section_table(str_data, idx):
    return [float(line.split(',')[idx]) for line in str_data.splitlines()]


class CrossSectionBaseCheck(BaseCheck):
    """Base class for all cross section definition checks."""

    # TODO: extend to work with all tables with cross sections
    # use self.table instead of models.CrossSectionLocation
    # adapt config.py

    def __init__(self, column, *args, **kwargs):
        self.shapes = kwargs.pop("shapes", None)
        super().__init__(column, *args, **kwargs)

    @property
    def shape_msg(self):
        if self.shapes is None:
            return ["all"]
        return sorted({x.value for x in self.shapes})

    def to_check(self, session):
        qs = super().to_check(session)
        if self.shapes is not None:
            qs = qs.filter(
                self.table.c.cross_section_shape.in_(self.shapes)
            )
        return qs

    def parse_cross_section_table(self, session, col: TableColumn):
        records = self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        )
        for record in records:
            try:
                if col == TableColumn.both:
                    width = parse_cross_section_table(getattr(record, self.column.name), TableColumn.width.value)
                    height = parse_cross_section_table(getattr(record, self.column.name), TableColumn.height.value)
                    values = (width, height)
                else:
                    values = parse_cross_section_table(getattr(record, self.column.name),  col.value)
                yield (record, values)  # Yield the parsed values as a generator
            except (IndexError, ValueError):
                continue  # Skip records with errors


class CrossSectionNullCheck(CrossSectionBaseCheck):
    """Check if width / height is not NULL or empty"""

    def get_invalid(self, session):
        return (
            self.to_check(session)
            .filter((self.column == None) | (self.column == ""))
            .all()
        )

    def description(self):
        return f"{self.column_name} cannot be null or empty for shapes {self.shape_msg}"


class CrossSectionExpectEmptyCheck(CrossSectionBaseCheck):
    """Check if width / height is NULL or empty"""

    def get_invalid(self, session):
        return (
            self.to_check(session)
            .filter((self.column != None) & (self.column != ""))
            .all()
        )

    def description(self):
        return f"{self.column_name} should be null or empty for shapes {self.shape_msg}"


class CrossSectionFloatCheck(CrossSectionBaseCheck):
    """Check that width / height is a valid non-negative float"""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                value = getattr(record, self.column.name)
            except ValueError:
                invalids.append(record)
            else:
                if value < 0:
                    invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be a positive number for shapes {self.shape_msg}"


class CrossSectionGreaterZeroCheck(CrossSectionBaseCheck):
    """Check that width / height is larger than 0"""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                value = getattr(record, self.column.name)
            except ValueError:
                continue

            if value <= 0:
                invalids.append(record)
        return invalids

    def description(self):
        return f"{self.column_name} should be greater than zero for shapes {self.shape_msg}"


class CrossSectionTableCheck(CrossSectionBaseCheck):
    """Tabulated definitions should use a space for separating the floats."""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                for line in getattr(record, self.column.name).splitlines():
                    line = line.split(',')
                    if len(line) != 2:
                        invalids.append(record)
                        break
                    for x in line:
                        float(x)
            except ValueError:
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should contain a space separated list of numbers for shapes {self.shape_msg}"


class CrossSectionIncreasingCheck(CrossSectionBaseCheck):
    """Tabulated definitions should have an increasing list of heights."""

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(session, col=TableColumn.height):
            if values != sorted(values):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be monotonically increasing for shapes {self.shape_msg}. Maybe the width and height have been interchanged?"


class CrossSectionFirstElementZeroCheck(CrossSectionBaseCheck):
    """Tabulated definitions should start at with 0 height."""

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(session, col=TableColumn.height):
            if abs(values[0]) != 0:
                invalids.append(record)

        return invalids

    def description(self):
        return f"The first element of {self.column_name} should equal 0 for shapes {self.shape_msg}. Note that heights are relative to 'reference_level'."


class CrossSectionFirstElementNonZeroCheck(CrossSectionBaseCheck):
    """Tabulated rectangles cannot start with 0 width."""

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(session, col=TableColumn.width):
            if abs(values[0]) <= 0:
                invalids.append(record)

        return invalids

    def description(self):
        return f"The first element of {self.column_name} must be larger than 0 for tabulated rectangle shapes. Consider using tabulated trapezium."


class CrossSectionYZHeightCheck(CrossSectionBaseCheck):
    """The height of an yz profile should include 0 and should not have negative
    elements.
    """

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(session, col=TableColumn.height):
            if any(x < 0 for x in values) or not any(x == 0 for x in values):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} for YZ profiles should include 0.0 and should not include negative values."


class CrossSectionYZCoordinateCountCheck(CrossSectionBaseCheck):
    """yz profiles should have 3 coordinates (excluding a closing coordinate)"""


    def get_invalid(self, session):
        invalids = []
        for record, (widths, heights) in self.parse_cross_section_table(session, col=TableColumn.both):
            if len(widths) == 0 or len(widths) != len(heights):
                continue
            is_closed = widths[0] == widths[-1] and heights[0] == heights[-1]
            if len(heights) < (4 if is_closed else 3):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.table.name} width and height should contain at least 3 coordinates (excluding closing coordinate) for YZ profiles"


class CrossSectionYZIncreasingWidthIfOpenCheck(CrossSectionBaseCheck):
    """yz profiles should have increasing widths (y) if they are open"""


    def get_invalid(self, session):
        invalids = []
        for record, (widths, heights) in self.parse_cross_section_table(session, col=TableColumn.both):
            if widths[0] == widths[-1] and heights[0] == heights[-1]:
                continue
            elif len(widths) > 1 and any(
                previous_width >= next_width
                for (previous_width, next_width) in zip(widths[:-1], widths[1:])
            ):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be strictly increasing for open YZ profiles. Perhaps this is actually a closed profile?"


def cross_section_configuration(shape, width, height):
    """
    Calculate maximum width, maximum heigth  and open/closed configuration for cross-sections.
    If the heights or widths list is empty, but will be called, it is set to [] to avoid ValueErrors.
    A different checks will error on the empty list instead so the user knows to fix it.
    """
    if shape.is_tabulated:
        raise ValueError("cross_section_configuration cannot handle tabulated shaptes")
    max_width = 0 if not width else width
    if shape == constants.CrossSectionShape.CLOSED_RECTANGLE:
        max_height = 0 if not height else height
    elif shape == constants.CrossSectionShape.RECTANGLE:
        max_height = height
    elif shape == constants.CrossSectionShape.CIRCLE:
        max_height = max_width
    elif shape in [
        constants.CrossSectionShape.EGG,
        constants.CrossSectionShape.INVERTED_EGG,
    ]:
        max_height = 1.5 * max_width
    configuration = "closed" if shape.is_closed else "open"
    return max_width, max_height, configuration


def cross_section_configuration_tabulated(shape, widths, heights):
    """
    Calculate maximum width, maximum heigth  and open/closed configuration for cross-sections.
    If the heights or widths list is empty, but will be called, it is set to [] to avoid ValueErrors.
    A different checks will error on the empty list instead so the user knows to fix it.
    """
    if not shape.is_tabulated:
        raise ValueError("cross_section_configuration_tabulated can only handle tabulated shaptes")
    # TODO: update docstring
    if not widths:
        widths = [0]
    if not heights:
        heights = [0]
    if shape in [
        constants.CrossSectionShape.TABULATED_RECTANGLE,
        constants.CrossSectionShape.TABULATED_TRAPEZIUM,
    ]:
        last_width = widths[-1]
        max_height = max(heights)
        max_width = max(widths)
        if last_width == 0:
            configuration = "closed"
        elif last_width > 0:
            configuration = "open"
    elif shape == constants.CrossSectionShape.TABULATED_YZ:
        # without the rounding, floating-point errors occur
        max_width = round((max(widths) - min(widths)), 9)
        max_height = round((max(heights) - min(heights)), 9)
        first_width = widths[0]
        last_width = widths[-1]
        first_height = heights[0]
        last_height = heights[-1]
        if (first_width, first_height) == (last_width, last_height):
            configuration = "closed"
        else:
            configuration = "open"
    return max_width, max_height, configuration


class CrossSectionMinimumDiameterCheck(CrossSectionBaseCheck):
    """Check if cross section widths and heights are large enough"""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session):
            if record.cross_section_shape.is_tabulated:
                try:
                    widths = parse_cross_section_table(record.cross_section_table, TableColumn.width)
                    heights = parse_cross_section_table(record.cross_section_table, TableColumn.height)
                except ValueError:
                    continue  # other check catches this
                max_width, max_height, configuration = cross_section_configuration_tabulated(
                    shape=record.cross_section_shape,
                    widths=widths,
                    heights=heights
                )
            else:
                max_width, max_height, configuration = cross_section_configuration(
                    shape=record.cross_section_shape,
                    width=record.cross_section_width,
                    height=record.cross_section_height
                )
            # See nens/threedi-modelchecker#251
            minimum_diameter = 0.1
            if configuration == "closed":
                if (max_height < minimum_diameter) or (max_width < minimum_diameter):
                    invalids.append(record)
            # the profile height does not need checking on an open cross-section
            elif configuration == "open":
                if max_width < minimum_diameter:
                    invalids.append(record)

        return invalids

    def description(self):
        return f"{self.table.__tablename__}.cross_section_width and/or cross_section_height should be at least 0.1m"


class OpenIncreasingCrossSectionConveyanceFrictionCheck(CrossSectionBaseCheck):
    """
    Check if cross sections used with friction with conveyance
    are open and monotonically increasing in width
    """

    # TODO: modify for other tables - use column from arguments

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionLocation.id, *args, **kwargs)

    def get_invalid(self, session):
        invalids = []
        # todo: make generic (for some reason self.table.c results in failing tests)
        for record in session.execute(
            select(
                models.CrossSectionLocation.id,
                models.CrossSectionLocation.friction_type,
                models.CrossSectionLocation.cross_section_shape,
                models.CrossSectionLocation.cross_section_width,
                models.CrossSectionLocation.cross_section_height,
            ).where(
                    self.table.c.friction_type.in_(
                        [
                            constants.FrictionType.CHEZY_CONVEYANCE,
                            constants.FrictionType.MANNING_CONVEYANCE,
                        ]
                    )
                )
            )
        ):
            try:
                widths = [float(x) for x in record.cross_section_width.split(" ")]
                heights = (
                    [float(x) for x in record.cross_section_height.split(" ")]
                    if record.cross_section_height not in [None, ""]
                    else []
                )
            except ValueError:
                continue  # other check catches this

            _, _, configuration = cross_section_configuration(shape=record.cross_section_shape.value, width=widths,
                                                              height=heights)

            # friction with conveyance can only be used for cross-sections
            # which are open *and* have a monotonically increasing width
            if configuration == "closed" or (
                len(widths) > 1
                and any(
                    next_width < previous_width
                    for (previous_width, next_width) in zip(widths[:-1], widths[1:])
                )
            ):
                invalids.append(record)

        return invalids

    def description(self):
        return (
            "v2_cross_section_location.friction_type can only "
            "have conveyance if the associated definition is "
            "an open shape, and its width is monotonically increasing"
        )


class CrossSectionVariableCorrectLengthCheck(CrossSectionBaseCheck):
    """Variable friction and vegetation properties should contain 1 value for each element; len(var_property) = len(width)-1"""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column.name != None) & (self.column.name != "")
        ):
            try:
                # only take widths because another check already ensures len(widths) = len(heights)
                widths = [float(x) for x in record.cross_section_width.split(" ")]
                values = [
                    float(x) for x in getattr(record, self.column.name).split(" ")
                ]
            except ValueError:
                continue  # other check catches this
            if not (len(widths) - 1 == len(values)):
                invalids.append(record)
        return invalids

    def description(self):
        return f"{self.column_name} should contain 1 value for each element; len({self.column_name}) = len(width)-1"


class CrossSectionVariableRangeCheck(CrossSectionBaseCheck):
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
        str_parts = []
        if min_value is None:
            self.min_valid = lambda x: True
        else:
            self.min_valid = (
                (lambda x: x >= min_value)
                if left_inclusive
                else (lambda x: x > min_value)
            )
            str_parts.append(f"{'< ' if left_inclusive else '<= '}{min_value}")
        if max_value is None:
            self.max_valid = lambda x: True
        else:
            self.max_valid = (
                (lambda x: x <= max_value)
                if right_inclusive
                else (lambda x: x < max_value)
            )
            str_parts.append(f"{'> ' if right_inclusive else '>= '}{max_value}")
        self.range_str = " and/or ".join(str_parts)
        self.message = message
        super().__init__(*args, **kwargs)

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                values = [
                    float(x) for x in getattr(record, self.column.name).split(" ")
                ]
            except ValueError:
                invalids.append(record)
            if not self.min_valid(min(values)):
                invalids.append(record)
            elif not self.max_valid(max(values)):
                invalids.append(record)
        return invalids

    def description(self):
        if self.message is None:
            return f"some values in {self.column_name} are {self.range_str}"
        else:
            return self.message


class CrossSectionVariableFrictionRangeCheck(CrossSectionVariableRangeCheck):
    def __init__(
        self,
        friction_types,
        *args,
        **kwargs,
    ):
        self.friction_types = friction_types
        super().__init__(*args, **kwargs)

    def get_invalid(self, session):
        invalids = []
        records = set(
            self.to_check(session)
            .filter(
                models.CrossSectionLocation.friction_type.in_(self.friction_types)
                & models.CrossSectionLocation.cross_section_friction_values.is_not(None)
            )
            .filter((self.column != None) & (self.column != ""))
            .all()
        )
        for record in records:
            try:
                values = [
                    float(x) for x in getattr(record, self.column.name).split(" ")
                ]
            except ValueError:
                continue
            if not self.min_valid(min(values)):
                invalids.append(record)
            elif not self.max_valid(max(values)):
                invalids.append(record)
        return invalids

    def description(self):
        return f"some values in {self.column_name} are {self.range_str}, which is not allowed for friction type(s) {self.friction_types}"


class OpenIncreasingCrossSectionVariableCheck(CrossSectionBaseCheck):
    """
    Check if cross sections used with friction with conveyance
    are open and monotonically increasing in width
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            shapes=(constants.CrossSectionShape.TABULATED_YZ,), *args, **kwargs
        )

    def get_invalid(self, session):
        invalids = []
        records = self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        )
        for record in records:
            try:
                # Only used for TABULATED_YZ
                widths = [float(x) for x in record.cross_section_width.split(" ")]
                heights = [float(x) for x in record.cross_section_height.split(" ")]
            except ValueError:
                continue  # other check catches this

            _, _, configuration = cross_section_configuration(shape=record.cross_section_shape.value, width=widths,
                                                              height=heights)

            # friction with conveyance can only be used for cross-sections
            # which are open *and* have a monotonically increasing width
            if configuration == "closed" or (
                len(widths) > 1
                and any(
                    next_width < previous_width
                    for (previous_width, next_width) in zip(widths[:-1], widths[1:])
                )
            ):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} can only be used in an open channel with monotonically increasing width values"
