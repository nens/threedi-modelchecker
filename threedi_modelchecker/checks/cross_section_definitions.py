from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Union

from sqlalchemy import func
from threedi_schema import constants, models

from .base import BaseCheck


class CrossSectionTableColumnIdx(IntEnum):
    height = 0
    width = 1
    all = 2


class CrossSectionTableXYColumnIdx(IntEnum):
    Y = 0
    Z = 1
    all = 2


def parse_csv_table_col(str_data, idx):
    return [float(line.split(",")[idx]) for line in str_data.splitlines()]


def parse_csv_table(str_data):
    return [[float(item) for item in line.split(",")] for line in str_data.splitlines()]


class CrossSectionBaseCheck(BaseCheck):
    """Base class for all cross section definition checks."""

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
            qs = qs.filter(self.table.c.cross_section_shape.in_(self.shapes))
        return qs

    def parse_cross_section_vegetation_table(self, session):
        column = models.CrossSectionLocation.cross_section_vegetation_table
        records = self.to_check(session).filter((column != None) & (column != ""))
        for record in records:
            try:
                table = parse_csv_table(getattr(record, column.name))
                if len(table[0]) != 4:
                    raise ValueError(
                        "cross_section_vegetation_table must have 4 columns"
                    )
                yield (record, table)
            except (IndexError, ValueError):
                continue  # Skip records with errors

    def parse_cross_section_table(
        self,
        session,
        col_idx: Union[CrossSectionTableColumnIdx, CrossSectionTableXYColumnIdx],
    ):
        column = self.table.c.cross_section_table
        records = self.to_check(session).filter((column != None) & (column != ""))
        for record in records:
            try:
                if col_idx.name == "all":
                    str = getattr(record, column.name)
                    values = tuple(
                        [
                            parse_csv_table_col(str, _col_idx.value)
                            for _col_idx in type(col_idx)
                            if _col_idx != col_idx
                        ]
                    )
                else:
                    values = parse_csv_table_col(
                        getattr(record, column.name), col_idx.value
                    )
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


class CrossSectionCSVFormatCheck(CrossSectionBaseCheck):
    """Check whether each row in the string can be converted to a list of floats"""

    ncol = None
    nrow = None

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                lines = getattr(record, self.column.name).splitlines()
                if self.nrow is not None and len(lines) != self.nrow:
                    invalids.append(record)
                    continue
                for line in lines:
                    line = line.split(",")
                    if self.ncol is not None and len(line) != self.ncol:
                        invalids.append(record)
                        break
                    for x in line:
                        float(x)
            except ValueError:
                invalids.append(record)

        return invalids

    def description(self):
        return (
            f"{self.table.name}.{self.column_name} should contain one or more lines of "
            "comma separated values"
        )


class CrossSectionListCheck(CrossSectionCSVFormatCheck):
    nrow = 1

    def description(self):
        return (
            f"{self.table.name}.{self.column_name} should contain comma separated floats "
            f"for shapes {self.shape_msg}"
        )


class CrossSectionTableCheck(CrossSectionCSVFormatCheck):
    """Check whether each row in the table contains a list of ncols comma separated floats"""

    def __init__(self, ncol, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ncol = ncol

    def description(self):
        return (
            f"{self.column_name} should contain a csv table containing "
            f"{self.ncol} columns with floats for shapes {self.shape_msg}"
        )


class CrossSectionIncreasingCheck(CrossSectionBaseCheck):
    """Tabulated definitions should have an increasing list of heights."""

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableColumnIdx.height
        ):
            if values != sorted(values):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be monotonically increasing for shapes {self.shape_msg}. Maybe the width and height have been interchanged?"


class CrossSectionFirstElementZeroCheck(CrossSectionBaseCheck):
    """Tabulated definitions should start at with 0 height."""

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableColumnIdx.height
        ):
            if abs(values[0]) != 0:
                invalids.append(record)

        return invalids

    def description(self):
        return f"The first element of {self.column_name} should equal 0 for shapes {self.shape_msg}. Note that heights are relative to 'reference_level'."


class CrossSectionFirstElementNonZeroCheck(CrossSectionBaseCheck):
    """Tabulated rectangles cannot start with 0 width."""

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableColumnIdx.width
        ):
            if abs(values[0]) <= 0:
                invalids.append(record)

        return invalids

    def description(self):
        return f"The first element of {self.column_name} must be larger than 0 for tabulated rectangle shapes. Consider using tabulated trapezium."


class CrossSectionYZHeightCheck(CrossSectionBaseCheck):
    """The height of a yz profile should include 0 and should not have negative
    elements.
    """

    def get_invalid(self, session):
        invalids = []
        for record, values in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableXYColumnIdx.Z
        ):
            if any(x < 0 for x in values) or not any(x == 0 for x in values):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} for YZ profiles should include 0.0 and should not include negative values."


class CrossSectionYZCoordinateCountCheck(CrossSectionBaseCheck):
    """yz profiles should have 3 coordinates (excluding a closing coordinate)"""

    def get_invalid(self, session):
        invalids = []
        for record, (Y, Z) in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableXYColumnIdx.all
        ):
            if len(Y) == 0 or len(Y) != len(Z):
                continue
            is_closed = Z[0] == Z[-1] and Y[0] == Y[-1]
            if len(Z) < (4 if is_closed else 3):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.table.name} width and height should contain at least 3 coordinates (excluding closing coordinate) for YZ profiles"


class CrossSectionYZIncreasingWidthIfOpenCheck(CrossSectionBaseCheck):
    """yz profiles should have increasing widths (y) if they are open"""

    def get_invalid(self, session):
        invalids = []
        for record, (Y, Z) in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableXYColumnIdx.all
        ):
            if Y[0] == Y[-1] and Z[0] == Z[-1]:
                continue
            elif len(Y) > 1 and any(
                previous_width >= next_width
                for (previous_width, next_width) in zip(Y[:-1], Y[1:])
            ):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be strictly increasing for open YZ profiles. Perhaps this is actually a closed profile?"


def get_widths_heights_for_tabulated_record(record):
    if not record.cross_section_shape.is_tabulated:
        raise ValueError(
            "get_widths_heighs_for_tabulated_record cannot handle tabulated shaptes"
        )
    if record.cross_section_shape == constants.CrossSectionShape.TABULATED_YZ:
        widths = parse_csv_table_col(
            record.cross_section_table, CrossSectionTableXYColumnIdx.Y
        )
        heights = parse_csv_table_col(
            record.cross_section_table, CrossSectionTableXYColumnIdx.Z
        )
    else:
        widths = parse_csv_table_col(
            record.cross_section_table, CrossSectionTableColumnIdx.width
        )
        heights = parse_csv_table_col(
            record.cross_section_table, CrossSectionTableColumnIdx.height
        )
    return widths, heights


def cross_section_configuration_for_record(record):
    if record.cross_section_shape.is_tabulated:
        widths, heights = get_widths_heights_for_tabulated_record(record)
        return cross_section_configuration_tabulated(
            shape=record.cross_section_shape, widths=widths, heights=heights
        )
    else:
        return cross_section_configuration_not_tabulated(
            shape=record.cross_section_shape,
            width=record.cross_section_width,
            height=record.cross_section_height,
        )


def cross_section_configuration_not_tabulated(shape, width, height):
    """
    Retrieve maximum width, maximum height  and open/closed configuration for not tabulated
    cross-sections.
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
    Retrieve maximum width, maximum height  and open/closed configuration for tabulated cross-sections.
    """
    if not shape.is_tabulated:
        raise ValueError(
            "cross_section_configuration_tabulated can only handle tabulated shaptes"
        )
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
        else:
            raise ValueError(
                "A tabulated rectangle or trapezium cannot have a negative last width"
            )
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
    else:
        raise ValueError(
            "cross_section_configuration_tabulated was called for a tabulated shape other "
            "than TABULATED_YZ, TABULATED_RECTANGLE or TABULATED_TRAPEZIUM"
        )
    return max_width, max_height, configuration


class CrossSectionMinimumDiameterCheck(CrossSectionBaseCheck):
    """Check if cross section widths and heights are large enough"""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session):
            (
                max_width,
                max_height,
                configuration,
            ) = cross_section_configuration_for_record(record)
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
        return f"{self.table.name}.cross_section_width and/or cross_section_height should be at least 0.1m"


class OpenIncreasingCrossSectionCheck(CrossSectionBaseCheck):
    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session):
            # friction with conveyance can only be used for cross-sections
            # which are open *and* have a monotonically increasing width
            if record.cross_section_shape.is_tabulated:
                if (
                    record.cross_section_shape
                    == constants.CrossSectionShape.TABULATED_YZ
                ):
                    widths = parse_csv_table_col(
                        record.cross_section_table, CrossSectionTableXYColumnIdx.Y.value
                    )
                else:
                    widths = parse_csv_table_col(
                        record.cross_section_table, CrossSectionTableColumnIdx.width
                    )
                if any(
                    next_width < previous_width
                    for (previous_width, next_width) in zip(widths[:-1], widths[1:])
                ):
                    invalids.append(record)
                    continue
            _, _, configuration = cross_section_configuration_for_record(record)
            if configuration == "closed":
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} can only be used in an open channel with monotonically increasing width values"


class OpenIncreasingCrossSectionConveyanceFrictionCheck(
    OpenIncreasingCrossSectionCheck
):
    """
    Check if cross sections used with friction with conveyance
    are open and monotonically increasing in width
    """

    def to_check(self, session):
        return (
            super()
            .to_check(session)
            .where(
                self.table.c.cross_section_shape.isnot(None),
                self.table.c.friction_type.in_(
                    [
                        constants.FrictionType.CHEZY_CONVEYANCE,
                        constants.FrictionType.MANNING_CONVEYANCE,
                    ]
                ),
            )
        )

    def description(self):
        return (
            f"{self.table.name}.friction_type can only "
            "have conveyance if the associated definition is "
            "an open shape, and its width is monotonically increasing"
        )


class OpenIncreasingCrossSectionVariableCheck(OpenIncreasingCrossSectionCheck):
    """
    Check if cross sections used with friction with conveyance
    are open and monotonically increasing in width
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            shapes=(constants.CrossSectionShape.TABULATED_YZ,), *args, **kwargs
        )

    def description(self):
        return f"{self.column_name} can only be used in an open channel with monotonically increasing width values"


class CrossSectionVariableCorrectLengthCheck(CrossSectionBaseCheck, ABC):
    """Variable friction and vegetation properties should contain 1 value for each element; len(var_property) = len(width)-1"""

    @abstractmethod
    def parse_str_value(self, variable):
        return

    def get_invalid(self, session):
        invalids = []
        for record, widths in self.parse_cross_section_table(
            session, col_idx=CrossSectionTableColumnIdx.width
        ):
            try:
                values = self.parse_str_value(getattr(record, self.column.name))

            except ValueError:
                continue  # other check catches this
            if not (len(widths) - 1 == len(values)):
                invalids.append(record)
        return invalids

    def description(self):
        return f"{self.column_name} should contain 1 value for each element."


class OpenIncreasingCrossSectionConveyanceFrictionCheckWithMaterial(
    OpenIncreasingCrossSectionCheck
):
    """
    Check if cross sections used with friction with conveyance
    are open and monotonically increasing in width
    """

    def to_check(self, session):
        return (
            super()
            .to_check(session)
            .outerjoin(models.Material, self.table.c.material_id == models.Material.id)
            .where(
                self.table.c.cross_section_shape.isnot(None),
                # take value from table if present, otherwise value from Material
                func.coalesce(
                    self.table.c.friction_type, models.Material.friction_type
                ).in_(
                    [
                        constants.FrictionType.CHEZY_CONVEYANCE,
                        constants.FrictionType.MANNING_CONVEYANCE,
                    ]
                ),
            )
        )

    def description(self):
        return f"{self.column_name} should contain 1 value for each element; len({self.column_name}) = len(width)-1"


class CrossSectionFrictionCorrectLengthCheck(CrossSectionVariableCorrectLengthCheck):
    def parse_str_value(self, str_value):
        return [float(item) for item in str_value.split(",")]


class CrossSectionVegetationCorrectLengthCheck(CrossSectionVariableCorrectLengthCheck):
    def parse_str_value(self, str_value):
        return list(str_value.splitlines())


class CrossSectionVegetationTableNotNegativeCheck(CrossSectionBaseCheck):
    """Check for negative valuesin cross_section_vegetation_table"""

    def get_invalid(self, session):
        invalids = []
        for record, table in self.parse_cross_section_vegetation_table(session):
            if any(item < 0 for row in table for item in row):
                invalids.append(record)
        return invalids

    def description(self):
        return f"All values in {self.table.name}.{self.column_name} should be equal to or larger than 0"


class CrossSectionVariableFrictionRangeCheck(CrossSectionBaseCheck):
    def __init__(
        self,
        friction_types,
        min_value=None,
        max_value=None,
        left_inclusive=True,
        right_inclusive=True,
        message=None,
        *args,
        **kwargs,
    ):
        self.friction_types = friction_types
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
        records = (
            self.to_check(session)
            .filter((self.column != None) & (self.column != ""))
            .filter(
                models.CrossSectionLocation.friction_type.in_(self.friction_types)
                & models.CrossSectionLocation.cross_section_friction_values.is_not(None)
            )
        )
        for record in records:
            try:
                values = [
                    float(x) for x in getattr(record, self.column.name).split(",")
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
