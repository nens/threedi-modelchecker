from .base import BaseCheck
from ..threedi_model import models
from ..threedi_model import constants


class BankLevelCheck(BaseCheck):
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


from threedi_modelchecker.model_errors import InvalidCrossSectionShape
from ..threedi_model import models, constants


def query_invalid_bank_levels(session):
    """Cross_section_location.Bank_level cannot be null if calculation type
    of the channel is CONNECTED or DOUBLE_CONNECTED"""
    q = session.query(models.CrossSectionLocation).filter(
        models.CrossSectionLocation.bank_level == None,
        models.CrossSectionLocation.channel.has(
            models.Channel.calculation_type.in_(
                [constants.CalculationType.CONNECTED,
                constants.CalculationType.DOUBLE_CONNECTED]
            )
        ),
    )
    return q


def get_invalid_cross_section_shape_errors(session):
    q = session.query(models.CrossSectionDefinition)
    invalid_cross_section_errors = []
    for cross_section_definition in q.all():
        try:
            CrossSectionShapeValidator.validate(cross_section_definition)
        except InvalidCrossSectionShape as e:
            invalid_cross_section_errors.append(e)
    return invalid_cross_section_errors



# TODO: REWRITE TO A BASECHECK
class CrossSectionShapeValidator:
    """Class for grouping validation functions of cross section shape"""

    @classmethod
    def validate(cls, cross_section_definition):
        """Validate if an threedi-cross-section-definition shape is correct

        :param cross_section_defintion: models.CrossSectionDefinition
        :return True if valid
        :raise InvalidCrossSectionShape
        """
        cls.cross_section_definition = cross_section_definition
        shape = cross_section_definition.shape
        width = cross_section_definition.width
        height = cross_section_definition.height
        if shape == constants.CrossSectionShape.RECTANGLE:
            cls.validate_rectangle(width, height)
        elif shape == constants.CrossSectionShape.CIRCLE:
            cls.validate_circle(width)
        elif shape == constants.CrossSectionShape.EGG:
            cls.validate_egg(width, height)
        elif shape == constants.CrossSectionShape.TABULATED_RECTANGLE:
            cls.validate_tabulated_shape(width, height)
        elif shape == constants.CrossSectionShape.TABULATED_TRAPEZIUM:
            cls.validate_tabulated_shape(width, height)
        return True

    @classmethod
    def validate_rectangle(cls, width, height):
        cls.read_float(width)
        cls.read_float(height)

    @classmethod
    def validate_circle(cls, width):
        float(width)

    @classmethod
    def validate_egg(cls, width, height):
        heights = height.split(' ')
        widths = width.split(' ')
        if len(heights) != len(widths):
            raise InvalidCrossSectionShape(
                instance=cls.cross_section_definition,
                column=cls.cross_section_definition.shape,
                message="height and width should have equal number of elements"
            )
        for h, w in zip(heights, widths):
            cls.read_float(w)
            cls.read_float(h)

    @classmethod
    def validate_tabulated_shape(cls, width, height):
        heights = height.split(' ')
        widths = width.split(' ')
        if len(heights) != len(widths):
            raise InvalidCrossSectionShape(
                instance=cls.cross_section_definition,
                column=models.CrossSectionDefinition.shape,
                message="height and width should have equal number of elements"
            )
        for h, w in zip(heights, widths):
            cls.read_float(w)
            cls.read_float(h)

    @classmethod
    def read_float(cls, str_):
        try:
            return float(str_)
        except (ValueError, TypeError):
            raise InvalidCrossSectionShape(
                instance=cls.cross_section_definition,
                column=models.CrossSectionDefinition.shape,
                message="invalid value '%s', should contain a float" % str_
            )
