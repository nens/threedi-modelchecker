import pytest

from threedi_modelchecker.model_errors import InvalidCrossSectionShape
from threedi_modelchecker.specific_model_checks import (
    query_invalid_bank_levels,
    get_invalid_cross_section_shape_errors,
    CrossSectionShapeValidator)
from threedi_modelchecker.threedi_model import models, constants
from . import factories


def test_query_invalid_cross_section_location_bank_levels(session):
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

    q = query_invalid_bank_levels(session)
    assert q.count() == 1
    assert q.first().id == wrong.id


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

    errors = get_invalid_cross_section_shape_errors(session)
    assert len(errors) == 0


def test_CrossSectionShapeValidator_invalid_float():
    csd = factories.CrossSectionDefinitionFactory(
        width='1 2',
        height='a',
        shape=constants.CrossSectionShape.TABULATED_TRAPEZIUM
    )
    with pytest.raises(InvalidCrossSectionShape):
        CrossSectionShapeValidator.validate(csd)


def test_CrossSectionShapeValidator_invalid_lenths():
    csd = factories.CrossSectionDefinitionFactory(
        width='1 2',
        height='1 2 3',
        shape=constants.CrossSectionShape.TABULATED_RECTANGLE
    )
    with pytest.raises(InvalidCrossSectionShape):
        CrossSectionShapeValidator.validate(csd)
