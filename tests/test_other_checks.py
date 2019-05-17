import pytest

from threedi_modelchecker.model_errors import InvalidCrossSectionShape
from threedi_modelchecker.checks.other import CrossSectionShapeCheck
from threedi_modelchecker.checks.other import BankLevelCheck
from threedi_modelchecker.checks.other import valid_tabulated_shape
from threedi_modelchecker.checks.patterns import POSITIVE_FLOAT_LIST

from threedi_modelchecker.threedi_model import models, constants
from . import factories


def test_check_cross_section_location_bank_levels(session):
    channel = factories.ChannelFactory(
        calculation_type=constants.CalculationType.CONNECTED)
    wrong = factories.CrossSectionLocationFactory(
        channel=channel,
        bank_level=None
    )
    correct1 = factories.CrossSectionLocationFactory(
        channel=channel,
        bank_level=1.0
    )
    correct2 = factories.CrossSectionLocationFactory(
        channel=factories.ChannelFactory(
            calculation_type=constants.CalculationType.EMBEDDED),
        bank_level=None
    )

    bank_level_check = BankLevelCheck()
    invalid_bank_levels = bank_level_check.get_invalid(session)
    assert len(invalid_bank_levels) == 1
    assert invalid_bank_levels[0].id == wrong.id


def test_get_invalid_cross_section_shapes(session):
    factories.CrossSectionDefinitionFactory(
        width='1',
        height='1',
        shape=constants.CrossSectionShape.RECTANGLE
    )
    factories.CrossSectionDefinitionFactory(
        width='1',
        height=None,
        shape=constants.CrossSectionShape.CIRCLE
    )
    factories.CrossSectionDefinitionFactory(
        width='1 2',
        height='1 2',
        shape=constants.CrossSectionShape.TABULATED_TRAPEZIUM
    )

    coss_section_check = CrossSectionShapeCheck()
    invalid_rows = coss_section_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_valid_tabulated_shape():
    width = '0 1 2 3'
    height = '0 1 2 3'
    assert valid_tabulated_shape(width, height)


def test_valid_tabulated_shape_empty():
    assert not valid_tabulated_shape('', '')


def test_valid_tabulated_shape_unequal_length():
    width = '1 2'
    height = '1 2 3'
    assert not valid_tabulated_shape(width, height)


def test_valid_tabulated_shape_invalid_char():
    width = '1 2'
    height = '1 a'
    assert not valid_tabulated_shape(width, height)
