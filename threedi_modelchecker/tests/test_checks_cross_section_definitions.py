import pytest
from threedi_schema import constants, models

from threedi_modelchecker.checks.cross_section_definitions import (
    CrossSectionEqualElementsCheck,
    CrossSectionExpectEmptyCheck,
    CrossSectionFirstElementNonZeroCheck,
    CrossSectionFloatCheck,
    CrossSectionFloatListCheck,
    CrossSectionGreaterZeroCheck,
    CrossSectionIncreasingCheck,
    CrossSectionMinimumDiameterCheck,
    CrossSectionNullCheck,
    CrossSectionVariableCorrectLengthCheck,
    CrossSectionVariableFrictionRangeCheck,
    CrossSectionVariableRangeCheck,
    CrossSectionYZCoordinateCountCheck,
    CrossSectionYZHeightCheck,
    CrossSectionYZIncreasingWidthIfOpenCheck,
    OpenIncreasingCrossSectionConveyanceFrictionCheck,
    OpenIncreasingCrossSectionVariableCheck,
)

from . import factories


def test_in_use(session):
    # should only check records in use
    definition = factories.CrossSectionDefinitionFactory(
        width=None, shape=constants.CrossSectionShape.CIRCLE
    )

    check = CrossSectionNullCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0

    factories.CrossSectionLocationFactory(definition=definition)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_filter_shapes(session):
    # should only check records of given types
    definition = factories.CrossSectionDefinitionFactory(
        width=None, shape=constants.CrossSectionShape.CIRCLE
    )
    factories.CrossSectionLocationFactory(definition=definition)

    check = CrossSectionNullCheck(
        column=models.CrossSectionDefinition.width,
        shapes=[constants.CrossSectionShape.RECTANGLE],
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0

    check = CrossSectionNullCheck(
        column=models.CrossSectionDefinition.width,
        shapes=[constants.CrossSectionShape.CIRCLE],
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, ""])
def test_check_null_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionNullCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1

    check = CrossSectionExpectEmptyCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", [" "])
def test_check_null_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionNullCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0

    check = CrossSectionExpectEmptyCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [" ", "foo", "0,1", "1e-2e8", "-0.1"])
def test_check_float_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize(
    "width", [None, "", "2", "0.1", ".2", "7.", "1e-5", "1E+2", " 0.1"]
)
def test_check_float_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", ["0", " 0", "0.0", "-0", "-1.2"])
def test_check_greater_zero_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionGreaterZeroCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "foo", "0.1", "1e-2"])
def test_check_greater_zero_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionGreaterZeroCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", [" ", "0,1,2", "3;5;7", "foo"])
def test_check_float_list_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatListCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "0", "0.1", "0 1 2", "-.2 5.72 9. 1e2"])
def test_check_float_list_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFloatListCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", ["0", "0 1"])
def test_check_equal_elements_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width,
        height="0 2 5",
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionEqualElementsCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "3;5;7", "1 2 3"])
def test_check_equal_elements_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(
        width=width,
        height="0 2 5",
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionEqualElementsCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", ["2 1 4"])
def test_increasing_elements_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionIncreasingCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "3;5;7", "1 2 3"])
def test_increasing_elements_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionIncreasingCheck(column=models.CrossSectionDefinition.width)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("width", ["0 1 4"])
def test_first_nonzero_invalid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFirstElementNonZeroCheck(
        column=models.CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("width", [None, "", "3;5;7", "1 2 3"])
def test_first_nonzero_valid(session, width):
    definition = factories.CrossSectionDefinitionFactory(width=width)
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionFirstElementNonZeroCheck(
        column=models.CrossSectionDefinition.width
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("height", ["0 1 2", "0 1 1", "1 0 1", "foo", None, "0"])
def test_check_yz_height_valid(session, height):
    definition = factories.CrossSectionDefinitionFactory(
        width="1 2 3",
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionYZHeightCheck(column=models.CrossSectionDefinition.height)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize("height", ["1 2 3", "0 -1 1"])
def test_check_yz_height_invalid(session, height):
    definition = factories.CrossSectionDefinitionFactory(
        width="1 2 3",
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionYZHeightCheck(column=models.CrossSectionDefinition.height)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize(
    "width,height",
    [
        # ("0 0.5 1 1.5", "0.5 0 0 0.5"),
        ("0 0.5", "0.5 0"),
        ("0 0.5 0", "0.5 0 0.5"),
    ],
)
def test_check_yz_coord_count_invalid(session, width, height):
    definition = factories.CrossSectionDefinitionFactory(
        width=width,
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionYZCoordinateCountCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize(
    "width,height",
    [
        ("0 0.5 1 1.5", "0.5 0 0 0.5"),
        ("0.5 0 0.5 1.5 1.5 0.5", "0 1 2 2 0 0"),
        ("foo", ""),
        ("0 0.5", "0.5"),
        ("0 0.5 1 1.5 2.0", "0.5 0 0 0.5"),
    ],
)
def test_check_yz_coord_count_valid(session, width, height):
    definition = factories.CrossSectionDefinitionFactory(
        width=width,
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionYZCoordinateCountCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize(
    "width,height",
    [
        ("0 0.5 1 1", "0.5 0 0 0.5"),
        ("0.5 0 0.5 1.5 1.5 0.5", "0 1 2 2 0 1"),
    ],
)
def test_check_yz_increasing_if_open_invalid(session, width, height):
    definition = factories.CrossSectionDefinitionFactory(
        width=width,
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionYZIncreasingWidthIfOpenCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize(
    "width,height",
    [
        ("0 0.5 1 1.5", "0.5 0 0 0.5"),
        ("0.5 0 0.5 1.5 1.5 0.5", "0 1 2 2 0 0"),
        ("foo", ""),
        ("0 0.5", "0.5"),
        ("0 0.5 1 1.5 2.0", "0.5 0 0 0.5"),
    ],
)
def test_check_yz_increasing_if_open_valid(session, width, height):
    definition = factories.CrossSectionDefinitionFactory(
        width=width,
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionYZIncreasingWidthIfOpenCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize(
    "shape,width,height,expected_result",
    [
        (0, "0.1", "0.2", 0),  # closed rectangle, sufficient width and height, pass
        (0, "0.05", "0.2", 1),  # closed rectangle, insufficient width, fail
        (0, "0.1", "0.03", 1),  # closed rectangle, insufficient height, fail
        (1, "0.1", None, 0),  # open rectangle, sufficient width, no height, pass
        (
            1,
            "0.1",
            "0.03",
            0,
        ),  # open rectangle, sufficient width, insufficient height should be ignored, pass
        (1, "0.05", "0.2", 1),  # open rectangle, insufficient width, fail
        (
            2,
            "0.2",
            "0.05",
            0,
        ),  # circle, insufficient height should be overwritten by width, pass
        (2, "0.05", "0.2", 1),  # circle, insufficient width, fail
        (
            3,
            "0.1",
            "0.03",
            0,
        ),  # egg, insufficient height should be overwritten by 1.5 * width, pass
        (3, "0.05", "0.2", 1),  # egg, insufficient width, fail
        (
            8,
            "0.1",
            "0.03",
            0,
        ),  # inverted egg, insufficient height should be overwritten by 1.5 * width, pass
        (8, "0.05", "0.2", 1),  # inverted egg, insufficient width, fail
        (
            5,
            "0.04 0.1",
            "0.06 0.2",
            0,
        ),  # open tabulated rectangle, sufficient width and height, pass
        (
            5,
            "0.04 0.05",
            "0.06 0.2",
            1,
        ),  # open tabulated rectangle, insufficient width, fail
        (
            5,
            "0.04 0.1",
            "0.06 0.03",
            0,
        ),  # open tabulated rectangle, insufficient height, should be ignored, pass
        (
            5,
            "0.04 0.1 0",
            "0.06 0.2",
            0,
        ),  # closed tabulated rectangle, sufficient width and height, pass
        (
            5,
            "0.04 0.05 0",
            "0.06 0.2",
            1,
        ),  # closed tabulated rectangle, insufficient width, fail
        (
            5,
            "0.04 0.1 0",
            "0.06 0.03",
            1,
        ),  # closed tabulated rectangle, insufficient height, fail
        (
            6,
            "0.04 0.1",
            "0.06 0.2",
            0,
        ),  # open tabulated trapezium, sufficient width and height, pass
        (
            6,
            "0.04 0.05",
            "0.06 0.2",
            1,
        ),  # open tabulated trapezium, insufficient width, fail
        (
            6,
            "0.04 0.1",
            "0.06 0.03",
            0,
        ),  # open tabulated trapezium, insufficient height, should be ignored, pass
        (
            6,
            "0.04 0.1 0",
            "0.06 0.2",
            0,
        ),  # closed tabulated trapezium, sufficient width and height, pass
        (
            6,
            "0.04 0.05 0",
            "0.06 0.2",
            1,
        ),  # closed tabulated trapezium, insufficient width, fail
        (
            6,
            "0.04 0.1 0",
            "0.06 0.03",
            1,
        ),  # closed tabulated trapezium, insufficient height, fail
        (
            7,
            "0.01 0.11",
            "0.11 0.21",
            0,
        ),  # open tabulated yz, sufficient width and height, pass
        (7, "0.01 0.10", "0.11 0.21", 1),  # open tabulated yz, insufficient width, fail
        (
            7,
            "0.01 0.11",
            "0.11 0.20",
            0,
        ),  # open tabulated yz, insufficient height, should be ignored, pass
        (
            7,
            "0.01 0.11 0.01",
            "0.11 0.21 0.11",
            0,
        ),  # closed tabulated yz, sufficient width and height, pass
        (
            7,
            "0.01 0.10 0.01",
            "0.11 0.21 0.11",
            1,
        ),  # closed tabulated yz, insufficient width, fail
        (
            7,
            "0.01 0.11 0.01",
            "0.11 0.20 0.11",
            1,
        ),  # closed tabulated yz, insufficient height, fail
        (0, "foo", "", 0),  # bad data, pass
    ],
)
def test_check_cross_section_minimum_diameter(
    session, shape, width, height, expected_result
):
    definition = factories.CrossSectionDefinitionFactory(
        shape=shape,
        width=width,
        height=height,
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionMinimumDiameterCheck()
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == expected_result


@pytest.mark.parametrize(
    "shape,width,height,expected_result",
    [
        (0, "0.1", "0.2", 1),  # closed rectangle, fail
        (1, "0.1", None, 0),  # open rectangle, pass
        (
            5,
            "0.04 0.1",
            "0.06 0.2",
            0,
        ),  # open tabulated rectangle, increasing width, pass
        (
            5,
            "0.04 0.1 0.1",
            "0.06 0.2 0.3",
            0,
        ),  # open tabulated rectangle, equal width segments, pass
        (
            5,
            "0.2 0.1",
            "0.06 0.2",
            1,
        ),  # open tabulated rectangle, decreasing width, fail
        (
            5,
            "0.04 0.1 0",
            "0.06 0.2",
            1,
        ),  # closed tabulated rectangle, fail
        (
            6,
            "0.04 0.1",
            "0.06 0.2",
            0,
        ),  # open tabulated trapezium, increasing width, pass
        (
            6,
            "0.04 0.1 0.1",
            "0.06 0.2 0.3",
            0,
        ),  # open tabulated trapezium, equal width segments, pass
        (
            6,
            "0.2 0.1",
            "0.06 0.3",
            1,
        ),  # open tabulated trapezium, decreasing width, fail
        (
            6,
            "0.04 0.1 0",
            "0.06 0.2",
            1,
        ),  # closed tabulated trapezium, fail
        (
            7,
            "0.01 0.11",
            "0.11 0.21",
            0,
        ),  # open tabulated yz, increasing width, pass
        (
            7,
            "0.01 0.10 0.10",
            "0.11 0.21 0.31",
            0,
        ),  # open tabulated yz, equal width segments, pass
        (
            7,
            "0.11 0.01",
            "0.11 0.20",
            1,
        ),  # open tabulated yz, decreasing width, fail
        (
            7,
            "0.01 0.11 0.01",
            "0.11 0.21 0.11",
            1,
        ),  # closed tabulated yz,  fail
        (0, "foo", "", 0),  # bad data, pass
    ],
)
@pytest.mark.parametrize(
    "friction_type,conveyance",
    [
        (constants.FrictionType.CHEZY, False),
        (constants.FrictionType.MANNING, False),
        (constants.FrictionType.CHEZY_CONVEYANCE, True),
        (constants.FrictionType.MANNING_CONVEYANCE, True),
    ],
)
def test_check_cross_section_increasing_open_with_conveyance_friction(
    session, shape, width, height, expected_result, friction_type, conveyance
):
    definition = factories.CrossSectionDefinitionFactory(
        shape=shape,
        width=width,
        height=height,
    )
    factories.CrossSectionLocationFactory(
        definition=definition, friction_type=friction_type
    )
    check = OpenIncreasingCrossSectionConveyanceFrictionCheck()
    # this check should pass on cross-section locations which don't use conveyance,
    # regardless of their other parameters
    if not conveyance:
        expected_result = 0
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == expected_result


@pytest.mark.parametrize("data, result", [["1 2", True], ["1 2 3", False]])
def test_check_correct_length(session, data, result):
    definition = factories.CrossSectionDefinitionFactory(
        width="1 2 3", height="0 2 5", friction_values=data
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionVariableCorrectLengthCheck(
        column=models.CrossSectionDefinition.friction_values
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


@pytest.mark.parametrize(
    "min_value, max_value, left_incl, right_incl, result",
    [
        [0, 1, True, True, True],
        [0, 0.5, True, True, False],
        [0.5, 1, True, True, False],
        [0, 1, False, True, False],
        [0, 1, True, False, False],
        [0, None, True, True, True],
        [None, 1, True, True, True],
    ],
)
def test_check_var_range(session, min_value, max_value, left_incl, right_incl, result):
    definition = factories.CrossSectionDefinitionFactory(friction_values="0 1")
    factories.CrossSectionLocationFactory(definition=definition)
    check = CrossSectionVariableRangeCheck(
        column=models.CrossSectionDefinition.friction_values,
        min_value=min_value,
        max_value=max_value,
        left_inclusive=left_incl,
        right_inclusive=right_incl,
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


@pytest.mark.parametrize(
    "friction_types, result",
    [
        [[constants.FrictionType.MANNING], False],
        [[constants.FrictionType.CHEZY], True],
    ],
)
def test_check_friction_values_range(session, friction_types, result):
    definition = factories.CrossSectionDefinitionFactory(friction_values="0 2")
    factories.CrossSectionLocationFactory(
        definition=definition, friction_type=constants.FrictionType.MANNING
    )
    check = CrossSectionVariableFrictionRangeCheck(
        min_value=0,
        max_value=1,
        right_inclusive=False,
        error_code=9999,
        column=models.CrossSectionDefinition.friction_values,
        friction_types=friction_types,
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


@pytest.mark.parametrize(
    "width,height,result",
    [
        (
            "0.01 0.11",
            "0.11 0.21",
            True,
        ),  # open tabulated yz, increasing width, pass
        (
            "0.11 0.01",
            "0.11 0.20",
            False,
        ),  # open tabulated yz, decreasing width, fail
        (
            "0.01 0.11 0.01",
            "0.11 0.21 0.11",
            False,
        ),  # closed tabulated yz,  fail
    ],
)
def test_check_cross_section_increasing_open_with_variables(
    session, width, height, result
):
    definition = factories.CrossSectionDefinitionFactory(
        shape=constants.CrossSectionShape.TABULATED_YZ,
        width=width,
        height=height,
        friction_values="1",
    )
    factories.CrossSectionLocationFactory(definition=definition)
    check = OpenIncreasingCrossSectionVariableCheck(
        models.CrossSectionDefinition.friction_values
    )
    # this check should pass on cross-section locations which don't use conveyance,
    # regardless of their other parameters
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result
