from sqlalchemy.orm import Query
from threedi_schema import models

from .base import BaseCheck


class CrossSectionBaseCheck(BaseCheck):
    """Base class for all cross section definition checks."""

    def __init__(self, column, *args, **kwargs):
        self.shapes = kwargs.pop("shapes", None)
        super().__init__(column, *args, **kwargs)

    @property
    def shape_msg(self):
        if self.shapes is None:
            return "{all}"
        return {x.value for x in self.shapes}

    def to_check(self, session):
        qs = super().to_check(session)
        if self.shapes is not None:
            qs = qs.filter(models.CrossSectionDefinition.shape.in_(self.shapes))
        return qs.filter(
            models.CrossSectionDefinition.id.in_(
                Query(models.CrossSectionLocation.definition_id).union_all(
                    Query(models.Pipe.cross_section_definition_id),
                    Query(models.Culvert.cross_section_definition_id),
                    Query(models.Weir.cross_section_definition_id),
                    Query(models.Orifice.cross_section_definition_id),
                )
            )
        )


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
                value = float(getattr(record, self.column.name))
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
                value = float(getattr(record, self.column.name))
            except ValueError:
                continue

            if value <= 0:
                invalids.append(record)
        return invalids

    def description(self):
        return f"{self.column_name} should be greater than zero for shapes {self.shape_msg}"


class CrossSectionFloatListCheck(CrossSectionBaseCheck):
    """Tabulated definitions should use a space for separating the floats."""

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                [float(x) for x in getattr(record, self.column.name).split(" ")]
            except ValueError:
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should contain a space separated list of numbers for shapes {self.shape_msg}"


class CrossSectionEqualElementsCheck(CrossSectionBaseCheck):
    """Tabulated definitions should have equal numbers of width and height elements."""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionDefinition.width, *args, **kwargs)

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (models.CrossSectionDefinition.width != None)
            & (models.CrossSectionDefinition.width != "")
            & (models.CrossSectionDefinition.height != None)
            & (models.CrossSectionDefinition.height != "")
        ):
            try:
                widths = [float(x) for x in record.width.split(" ")]
                heights = [float(x) for x in record.height.split(" ")]
            except ValueError:
                continue  # other check catches this

            if len(widths) != len(heights):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.table.name} width and height should an equal number of elements for shapes {self.shape_msg}"


class CrossSectionIncreasingCheck(CrossSectionBaseCheck):
    """Tabulated definitions should have an increasing list of heights."""

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
                continue  # other check catches this

            if len(values) > 1 and any(
                x > y for (x, y) in zip(values[:-1], values[1:])
            ):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be monotonically increasing for shapes {self.shape_msg}. Maybe the width and height have been interchanged?"


class CrossSectionFirstElementZeroCheck(CrossSectionBaseCheck):
    """Tabulated definitions should start at with 0 height."""

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
                continue  # other check catches this

            if abs(values[0]) != 0:
                invalids.append(record)

        return invalids

    def description(self):
        return f"The first element of {self.column_name} should equal 0 for shapes {self.shape_msg}. Note that heights are relative to 'reference_level'."


class CrossSectionFirstElementNonZeroCheck(CrossSectionBaseCheck):
    """Tabulated rectangles cannot start with 0 width."""

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
                continue  # other check catches this

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
        for record in self.to_check(session).filter(
            (self.column != None) & (self.column != "")
        ):
            try:
                values = [
                    float(x) for x in getattr(record, self.column.name).split(" ")
                ]
            except ValueError:
                continue  # other check catches this

            if len(values) == 0:
                continue

            if any(x < 0 for x in values) or not any(x == 0 for x in values):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} for YZ profiles should include 0.0 and should not include negative values."


class CrossSectionYZCoordinateCountCheck(CrossSectionBaseCheck):
    """yz profiles should have 3 coordinates (excluding a closing coordinate)"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionDefinition.width, *args, **kwargs)

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (models.CrossSectionDefinition.width != None)
            & (models.CrossSectionDefinition.width != "")
            & (models.CrossSectionDefinition.height != None)
            & (models.CrossSectionDefinition.height != "")
        ):
            try:
                widths = [float(x) for x in record.width.split(" ")]
                heights = [float(x) for x in record.height.split(" ")]
            except ValueError:
                continue  # other check catches this

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

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionDefinition.width, *args, **kwargs)

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (models.CrossSectionDefinition.width != None)
            & (models.CrossSectionDefinition.width != "")
            & (models.CrossSectionDefinition.height != None)
            & (models.CrossSectionDefinition.height != "")
        ):
            try:
                widths = [float(x) for x in record.width.split(" ")]
                heights = [float(x) for x in record.height.split(" ")]
            except ValueError:
                continue  # other check catches this

            if widths[0] == widths[-1] and heights[0] == heights[-1]:
                continue
            elif len(widths) > 1 and any(
                x >= y for (x, y) in zip(widths[:-1], widths[1:])
            ):
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.column_name} should be monotonically increasing for open YZ profiles. Perhaps this is actually a closed profile?"


class CrossSectionMinimumDiameterCheck(CrossSectionBaseCheck):
    """Check if cross section widths and heights are large enough"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionDefinition.id, *args, **kwargs)

    def configuration_type(
        self, shape, first_width, last_width, first_height, last_height
    ):
        if (
            (shape in [0, 2, 3, 8])
            or (shape in [5, 6] and last_width == 0)
            or (
                shape == 7
                and ((first_width, first_height) == (last_width, last_height))
            )
        ):
            return "closed"
        elif (
            (shape == 1)
            or (shape in [5, 6] and last_width > 0)
            or (
                shape == 7
                and ((first_width, first_height) != (last_width, last_height))
            )
        ):
            return "open"
        else:
            return "open"

    def get_heights(self, shape, widths, heights):
        if shape == 2:
            heights = widths
        if shape in [3, 8]:
            heights = [1.5 * i for i in widths]

        first_width = widths[0]
        last_width = widths[-1]

        if shape == 7:
            max_width = round((max(widths) - min(widths)), 9)
        else:
            max_width = max(widths)

        if heights:
            first_height = heights[0]
            last_height = heights[-1]
            if shape == 7:
                max_height = round((max(heights) - min(heights)), 9)
            else:
                max_height = max(heights)
        else:
            first_height = None
            last_height = None
            max_height = None

        return first_height, last_height, max_height, first_width, last_width, max_width

    def get_invalid(self, session):
        invalids = []
        for record in self.to_check(session).filter(
            (models.CrossSectionDefinition.width != None)
            & (models.CrossSectionDefinition.width != "")
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

            (
                first_height,
                last_height,
                max_height,
                first_width,
                last_width,
                max_width,
            ) = self.get_heights(record.shape.value, widths, heights)

            configuration = self.configuration_type(
                shape=record.shape.value,
                first_width=first_width,
                last_width=last_width,
                first_height=first_height,
                last_height=last_height,
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
        return "The largest values in v2_cross_section_definition.width and (if the cross-section is closed) v2_cross_section_definition.height should be at least 0.1m"
