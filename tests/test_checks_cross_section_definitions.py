from . import factories
from .checks.cross_section_definitions import CrossSectionNullCheck, CrossSectionFirstElementNotZeroCheck, CrossSectionIncreasingCheck, CrossSectionEqualElementsCheck, CrossSectionFloatCheck, CrossSectionFloatListCheck
from threedi_modelchecker.threedi_model.constants import CrossSectionShape
from threedi_modelchecker.threedi_model.models import CrossSectionDefinition
import pytest


def test_in_use(session):
    # should only check records in use
    definition = factories.CrossSectionDefinitionFactory(
        width=None, shape=CrossSectionShape.CIRCLE
    )

    check = CrossSectionNullCheck(column=CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0

    factories.CrossSectionLocationFactory(definition=definition)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_filter_shapes(session):
    # should only check records of given types
    definition = factories.CrossSectionDefinitionFactory(
        width=None, shape=CrossSectionShape.CIRCLE
    )
    factories.CrossSectionLocationFactory(definition=definition)

    check = CrossSectionNullCheck(
        column=CrossSectionDefinition.width,
        shapes=[CrossSectionShape.RECTANGLE]
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0

    check = CrossSectionNullCheck(
        column=CrossSectionDefinition.width,
        shapes=[CrossSectionShape.CIRCLE]
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, ""])
def test_check_null_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionNullCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [" "])
def test_check_null_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionNullCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", [" ", "foo", "0,1", " 0.1", "1e-2e8"])
def test_check_float_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "2", "0.1", ".2", "7.", "1e-5", "1E+2", " 0.1"])
def test_check_float_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0



@pytest.mark.parametrize("width", [" ", "foo", "0,1", "1e-2e8", "0", "-0.1"])
def test_check_float_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [" ", "0,1,2", "3;5;7", "foo"])
def test_check_float_list_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatListCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "0", "0.1", "0 1 2", "-.2 5.72 9. 1e2"])
def test_check_float_list_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatListCheck(
        column=CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", ["0", "0 1"])
def test_check_equal_elements_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width, height="0 2 5",
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionEqualElementsCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "3;5;7", "1 2 3"])
def test_check_equal_elements_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width, height="0 2 5",
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionEqualElementsCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0



@pytest.mark.parametrize("width", ["2 1 4"])
def test_increasing_elements_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionIncreasingCheck(column=CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "3;5;7", "1 2 3"])
def test_increasing_elements_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionIncreasingCheck(column=CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0



@pytest.mark.parametrize("width", ["0 1 4", "1e-9 5 6"])
def test_first_nonzero_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFirstElementNotZeroCheck(column=CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "3;5;7", "1 2 3", "1e-7 2 3"])
def test_first_nonzero_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFirstElementNotZeroCheck(column=CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0
