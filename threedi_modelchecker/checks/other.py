from .base import BaseCheck
from ..threedi_model import models
from ..threedi_model import constants
from threedi_modelchecker.checks import patterns


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
    width_match = patterns.POSITIVE_FLOAT.fullmatch(width)
    if height:
        height_match = patterns.POSITIVE_FLOAT.fullmatch(height)
    else:
        height_match = True
    return width_match and height_match


def valid_circle(width, height):
    return patterns.POSITIVE_FLOAT.fullmatch(width)


def valid_egg(width, height):
    width_match = patterns.POSITIVE_FLOAT_LIST.fullmatch(width)
    height_match = patterns.POSITIVE_FLOAT_LIST.fullmatch(height)
    if not width_match or not height_match:
        return False
    return len(width.split(' ')) == len(height.split(' '))


def valid_tabulated_shape(width, height):
    width_match = patterns.POSITIVE_FLOAT_LIST.fullmatch(width)
    height_match = patterns.POSITIVE_FLOAT_LIST.fullmatch(height)
    if not width_match or not height_match:
        return False
    return len(width.split(' ')) == len(height.split(' '))


class TimeseriesCheck(BaseCheck):
    """Check that `column` has the time series pattern: digit,float\n


    """
    def get_invalid(self, session):
        # get the first one to determine the temporal interval
        temporal_interval = []
        invalid_timeseries = []
        timeseries = session.query(self.table).all()
        for timeserie in timeseries:
            if not patterns.TIMESERIES.fullmatch(timeserie):
                invalid_timeseries.append(timeserie)
            if not temporal_interval:
                temporal_interval = [time for time, *_ in patterns.SINGLE_TIMESERIES_ENTRY.findall(timeseries)]
            else:
                temporal_interval2 = [time for time, *_ in patterns.SINGLE_TIMESERIES_ENTRY.findall(timeseries)]
                if not temporal_interval == temporal_interval2:
                    invalid_timeseries.append(timeserie)

        return invalid_timeseries
