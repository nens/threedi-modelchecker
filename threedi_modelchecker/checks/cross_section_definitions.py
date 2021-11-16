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


IN_USE = models.CrossSectionDefinition.id.in_(
    Query(models.CrossSectionLocation.definition_id).union_all(
        Query(models.Pipe.cross_section_definition_id),
        Query(models.Culvert.cross_section_definition_id),
        Query(models.Weir.cross_section_definition_id),
        Query(models.Orifice.cross_section_definition_id),
    )
)


class CrossSectionWidthFloatCheck(BaseCheck):
    """Check if all CrossSectionDefinition of types RECTANGLE, CLOSED_RECTANGLE, CIRCLE
    have a valid width.
    """
    shapes = (
        constants.CrossSectionShape.RECTANGLE,
        constants.CrossSectionShape.CLOSED_RECTANGLE,
        constants.CrossSectionShape.CIRCLE
    )

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionDefinition.shape, *args, **kwargs)

    def to_check(self, session):
        qs = self.to_check(session)
        return qs.filter(
            models.CrossSectionDefinition.shape.in_(self.shapes) &
            models.CrossSectionDefinition.id.in_(
                Query(models.CrossSectionLocation.definition_id).union_all(
                    Query(models.Pipe.cross_section_definition_id),
                    Query(models.Culvert.cross_section_definition_id),
                    Query(models.Weir.cross_section_definition_id),
                    Query(models.Orifice.cross_section_definition_id),
                )
            )
        )


    def get_invalid(self, session):
        cross_section_definitions = self.to_check(session)
        invalids = []
        for record in cross_section_definitions.all():
            try:
                width = float(record.width)
            except (TypeError, ValueError):
                invalids.append(record)
                continue
            if width <= 0:
                invalids.append(record)

        return invalids

    def description(self):
        return f"{self.table.name} contains an invalid width"


class CrossSectionShapeCheck(BaseCheck):
    """Check if all CrossSectionDefinition.shape are valid"""

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.CrossSectionDefinition.shape, *args, **kwargs)

    def get_invalid(self, session):
        cross_section_definitions = self.to_check(session).filter(
            models.CrossSectionDefinition.id.in_(
                Query(models.CrossSectionLocation.definition_id).union_all(
                    Query(models.Pipe.cross_section_definition_id),
                    Query(models.Culvert.cross_section_definition_id),
                    Query(models.Weir.cross_section_definition_id),
                    Query(models.Orifice.cross_section_definition_id),
                )
            ),
        )
        invalid_cross_section_shapes = []

        for cross_section_definition in cross_section_definitions.all():
            shape = cross_section_definition.shape
            width = cross_section_definition.width
            height = cross_section_definition.height
            if shape == constants.CrossSectionShape.RECTANGLE:
                if not valid_rectangle(width, height):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.CLOSED_RECTANGLE:
                if not valid_closed_rectangle(width, height):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.CIRCLE:
                if not valid_circle(width):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.EGG:
                if not valid_egg(width):
                    invalid_cross_section_shapes.append(cross_section_definition)
            if shape == constants.CrossSectionShape.TABULATED_RECTANGLE:
                if not valid_tabulated_shape(width, height, is_rectangle=True):
                    invalid_cross_section_shapes.append(cross_section_definition)
            elif shape == constants.CrossSectionShape.TABULATED_TRAPEZIUM:
                if not valid_tabulated_shape(width, height, is_rectangle=False):
                    invalid_cross_section_shapes.append(cross_section_definition)
        return invalid_cross_section_shapes

    def description(self):
        return f"{self.table.name} contains an invalid width or height"

def valid_closed_rectangle(width, height):
    if width is None:  # width is required
        return False
    width_match = patterns.POSITIVE_FLOAT_REGEX.fullmatch(width)
    if height is None:  # height is required
        return False
    height_match = patterns.POSITIVE_FLOAT_REGEX.fullmatch(height)
    return width_match and height_match


def valid_rectangle(width, height):
    if width is None:  # width is required
        return False
    return patterns.POSITIVE_FLOAT_REGEX.fullmatch(width)


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


def valid_tabulated_shape(width, height, is_rectangle):
    """Return if the tabulated shape is valid.

    Validating that the strings `width` and `height` contain positive floats
    was previously done using a regex. However, experiments showed that
    trying to split the string and reading in the floats is much faster.

    :param width: string of widths
    :param height: string of heights
    :return: True if the shape if valid
    """
    if height is None or width is None:
        return False
    try:
        heights = [float(x) for x in height.split(" ")]
        widths = [float(x) for x in width.split(" ")]
    except ValueError:
        return False
        # raise SchematisationError(
        #     f"Unable to parse cross section definition width and/or height "
        #     f"(got: '{width}', '{height}')."
        # )
    if len(heights) == 0:
        return False
        # raise SchematisationError(
        #     f"Cross section definitions of tabulated type must have at least one "
        #     f"height element (got: {height})."
        # )
    if len(heights) != len(widths):
        return False
        # raise SchematisationError(
        #     f"Cross section definitions of tabulated type must have equal number of "
        #     f"height and width elements (got: {height}, {width})."
        # )
    if len(heights) > 1 and any(x > y for (x, y) in zip(heights[:-1], heights[1:])):
        return False
        # raise SchematisationError(
        #     f"Cross section definitions of tabulated type must have increasing heights "
        #     f"(got: {height})."
        # )
    if is_rectangle and abs(widths[0]) < 1e-7:
        return False

    return True

