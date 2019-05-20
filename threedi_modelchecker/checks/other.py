from collections import Counter

from threedi_modelchecker.checks import patterns
from .base import BaseCheck
from ..threedi_model import constants
from ..threedi_model import models


class BankLevelCheck(BaseCheck):
    """Check 'CrossSectionLocation.bank_level' is not null if
    calculation_type is CONNECTED or DOUBLE_CONNECTED.
    """
    def __init__(self):
        super().__init__(
            column=models.CrossSectionLocation.bank_level
        )

    def get_invalid(self, session):
        q = session.query(models.CrossSectionLocation).filter(
            models.CrossSectionLocation.bank_level == None,
            models.CrossSectionLocation.channel.has(
                models.Channel.calculation_type.in_(
                    [constants.CalculationType.CONNECTED,
                     constants.CalculationType.DOUBLE_CONNECTED]
                )
            ),
        )
        return q.all()


class CrossSectionShapeCheck(BaseCheck):
    """Check if all CrossSectionDefinition.shape are valid"""
    def __init__(self):
        super().__init__(
            column=models.CrossSectionDefinition.shape
        )

    def get_invalid(self, session):
        cross_section_definitions = session.query(
            models.CrossSectionDefinition
        )
        invalid_cross_section_shapes = []

        for cross_section_definition in cross_section_definitions.all():
            shape = cross_section_definition.shape
            width = cross_section_definition.width
            height = cross_section_definition.height
            if shape == constants.CrossSectionShape.RECTANGLE:
                if not valid_rectangle(width, height):
                    invalid_cross_section_shapes.append(
                        cross_section_definition)
            elif shape == constants.CrossSectionShape.CIRCLE:
                if not valid_circle(width, height):
                    invalid_cross_section_shapes.append(
                        cross_section_definition)
            elif shape == constants.CrossSectionShape.EGG:
                if not valid_egg(width, height):
                    invalid_cross_section_shapes.append(
                        cross_section_definition)
            if shape == constants.CrossSectionShape.TABULATED_RECTANGLE:
                if not valid_tabulated_shape(width, height):
                    invalid_cross_section_shapes.append(
                        cross_section_definition)
            elif shape == constants.CrossSectionShape.TABULATED_TRAPEZIUM:
                if not valid_tabulated_shape(width, height):
                    invalid_cross_section_shapes.append(
                        cross_section_definition
                    )
        return invalid_cross_section_shapes


def valid_rectangle(width, height):
    width_match = patterns.POSITIVE_FLOAT_REGEX.fullmatch(width)
    if height:
        height_match = patterns.POSITIVE_FLOAT_REGEX.fullmatch(height)
    else:
        height_match = True
    return width_match and height_match


def valid_circle(width, height):
    return patterns.POSITIVE_FLOAT_REGEX.fullmatch(width)


def valid_egg(width, height):
    width_match = patterns.POSITIVE_FLOAT_LIST_REGEX.fullmatch(width)
    height_match = patterns.POSITIVE_FLOAT_LIST_REGEX.fullmatch(height)
    if not width_match or not height_match:
        return False
    return len(width.split(' ')) == len(height.split(' '))


def valid_tabulated_shape(width, height):
    width_match = patterns.POSITIVE_FLOAT_LIST_REGEX.fullmatch(width)
    height_match = patterns.POSITIVE_FLOAT_LIST_REGEX.fullmatch(height)
    if not width_match or not height_match:
        return False
    return len(width.split(' ')) == len(height.split(' '))


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

            timesteps = {time for time, *_ in
                         patterns.TIMESERIE_ENTRY_REGEX.findall(
                             timeserie)}
            if not required_timesteps:
                # Assume the first timeserie defines the required timesteps.
                # All others should have the same timesteps.
                required_timesteps = timesteps
                continue
            if timesteps != required_timesteps:
                invalid_timeseries.append(row)

        return invalid_timeseries
