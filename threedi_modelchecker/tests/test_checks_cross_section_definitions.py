import pytest
from threedi_schema import constants, models

from threedi_modelchecker.checks.cross_section_definitions import (
    cross_section_configuration_for_record,
    cross_section_configuration_not_tabulated,
    cross_section_configuration_tabulated,
    CrossSectionExpectEmptyCheck,
    CrossSectionFirstElementNonZeroCheck,
    CrossSectionFirstElementZeroCheck,
    CrossSectionFloatCheck,
    CrossSectionGreaterZeroCheck,
    CrossSectionIncreasingCheck,
    CrossSectionMinimumDiameterCheck,
    CrossSectionNullCheck,
    CrossSectionTableCheck,
    CrossSectionTableColumnIdx,
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


@pytest.mark.parametrize(
    "cross_section_table, col_idx, expected",
    [
        ("0,0\n2,1\n4,2", CrossSectionTableColumnIdx.width, [0, 2, 4]),
        ("0,0\n2,1\n4,2", CrossSectionTableColumnIdx.height, [0, 1, 2]),
        ("0,0\n2,1\n4,2", CrossSectionTableColumnIdx.all, ([0, 2, 4], [0, 1, 2])),
        (
            "0,1",
            CrossSectionTableColumnIdx.width,
            [
                0,
            ],
        ),
        (
            "0,1",
            CrossSectionTableColumnIdx.height,
            [
                1,
            ],
        ),
        (
            "0,1",
            CrossSectionTableColumnIdx.all,
            (
                [
                    0,
                ],
                [
                    1,
                ],
            ),
        ),
        ("0\n1", CrossSectionTableColumnIdx.width, [0, 1]),
        ("0\n1", CrossSectionTableColumnIdx.height, []),
        ("foo", CrossSectionTableColumnIdx.height, []),
        ("0", CrossSectionTableColumnIdx.width, [0]),
        ("0", CrossSectionTableColumnIdx.height, []),
    ],
)
def test_parse_cross_section_table(session, cross_section_table, col_idx, expected):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    # can use any class here!
    check = CrossSectionFloatCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    values = list(check.parse_cross_section_table(session=session, col_idx=col_idx))
    if expected:
        assert values[0][1] == expected
    else:
        assert not values


def test_parse_cross_section_table_generator(session):
    tables = ["0,0\n2,1\n4,2", "0,0\n1,2\n2,4"]
    expected = [[0, 2, 4], [0, 1, 2]]
    for cross_section_table in tables:
        factories.CrossSectionLocationFactory(
            cross_section_table=cross_section_table,
        )
    # can use any class here!
    check = CrossSectionFloatCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    for i, (record, values) in enumerate(
        check.parse_cross_section_table(
            session=session, col_idx=CrossSectionTableColumnIdx.width
        )
    ):
        if expected:
            assert values == expected[i]


def test_filter_shapes(session):
    # should only check records of given types
    factories.CrossSectionLocationFactory(
        cross_section_width=None,
        cross_section_shape=constants.CrossSectionShape.CIRCLE,
    )
    check = CrossSectionNullCheck(
        column=models.CrossSectionLocation.cross_section_width,
        shapes=[constants.CrossSectionShape.RECTANGLE],
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0

    check = CrossSectionNullCheck(
        column=models.CrossSectionLocation.cross_section_width,
        shapes=[constants.CrossSectionShape.CIRCLE],
    )
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize(
    "cross_section_height, is_null, is_empty",
    [(None, True, False)],
)
def test_check_null_check(session, cross_section_height, is_null, is_empty):
    factories.CrossSectionLocationFactory(
        cross_section_height=cross_section_height,
    )
    check = CrossSectionNullCheck(
        column=models.CrossSectionLocation.cross_section_height
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 1) == is_null

    check = CrossSectionExpectEmptyCheck(
        column=models.CrossSectionLocation.cross_section_height
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 1) == is_empty


@pytest.mark.parametrize("width, valid", [(-1, False), (1, True)])
def test_check_float(session, width, valid):
    factories.CrossSectionLocationFactory(
        cross_section_width=width,
    )
    check = CrossSectionFloatCheck(
        column=models.CrossSectionLocation.cross_section_width
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize("width, valid", [(-1, False), (0, False), (1, True)])
def test_check_greater_zero(session, width, valid):
    factories.CrossSectionLocationFactory(
        cross_section_width=width,
    )
    check = CrossSectionGreaterZeroCheck(
        column=models.CrossSectionLocation.cross_section_width
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize(
    "cross_section_table",
    [" ", "0 1", "3;5", "foo", "1,2,3,4", "1,2\3,", "1,2\3", ",2", ",2\3,4"],
)
def test_check_table_invalid(session, cross_section_table):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionTableCheck(models.CrossSectionLocation.cross_section_table)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 1


@pytest.mark.parametrize("cross_section_table", [None, "", "0,1", "0,1\n0,1"])
def test_check_table_valid(session, cross_section_table):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionTableCheck(models.CrossSectionLocation.cross_section_table)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == 0


@pytest.mark.parametrize(
    "cross_section_table, valid", [("1,2\n1,1", False), ("1,1\n1,2", True)]
)
def test_increasing_elements(session, cross_section_table, valid):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionIncreasingCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize(
    "cross_section_table, valid", [("1,2\n1,1", False), ("1,0\n1,2", True)]
)
def test_first_element_zero_check(session, cross_section_table, valid):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionFirstElementZeroCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize("cross_section_table, valid", [("0,1", False), ("1,2", True)])
def test_first_nonzero(session, valid, cross_section_table):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionFirstElementNonZeroCheck(
        column=models.CrossSectionLocation.cross_section_table,
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize(
    "cross_section_table, valid",
    [
        ("0,0\n0,1\n,0,2", True),
        ("0,0", True),
        ("0,1\n0,2\n0,3", False),
        ("0,0\n0,-1\n0,1", False),
    ],
)
def test_check_yz_height(session, cross_section_table, valid):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionYZHeightCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize(
    "cross_section_table, valid",
    [
        ("0,0.5\n0.5,0", False),
        ("0,0.5\n0.5,0\n0,0.5", False),
        ("0,0.5\n0.5,0\n1,0\n1.5,0.5", True),
        ("0.5,0\n0,1\n0.5,2\n1.5,2\n1.5,0\n0.5,0", True),
    ],
)
def test_check_yz_coord_count(session, cross_section_table, valid):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionYZCoordinateCountCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize(
    "cross_section_table, valid",
    [
        ("0,0.5\n0.5,0\n1,0\n1,0.5", False),
        ("0.5,0\n0,1\n0.5,2\n1.5,2\n1.5,0\n0.5,1", False),
        ("0,0.5\n0.5,0\n1,0\n1.5,0.5", True),
        ("0.5,0\n0,1\n0.5,2\n1.5,2\n1.5,0\n0.5,0", True),
    ],
)
def test_check_yz_increasing_if_open(session, cross_section_table, valid):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
    )
    check = CrossSectionYZIncreasingWidthIfOpenCheck(
        column=models.CrossSectionLocation.cross_section_table
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == valid


@pytest.mark.parametrize(
    "shape,width,height,expected_result",
    [
        (
            constants.CrossSectionShape.RECTANGLE,
            "0.1",
            "0.2",
            0,
        ),  # closed rectangle, sufficient width and height, pass
        (
            constants.CrossSectionShape.CLOSED_RECTANGLE,
            "0.05",
            "0.2",
            1,
        ),  # closed rectangle, insufficient width, fail
        (
            constants.CrossSectionShape.CLOSED_RECTANGLE,
            "0.1",
            "0.03",
            1,
        ),  # closed rectangle, insufficient height, fail
        (
            constants.CrossSectionShape.RECTANGLE,
            "0.1",
            None,
            0,
        ),  # open rectangle, sufficient width, no height, pass
    ],
)
def test_check_cross_section_minimum_diameter(
    session, shape, width, height, expected_result
):
    factories.CrossSectionLocationFactory(
        cross_section_width=width,
        cross_section_height=height,
        cross_section_shape=shape,
    )
    check = CrossSectionMinimumDiameterCheck(column=models.CrossSectionLocation.id)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == expected_result


@pytest.mark.parametrize(
    "shape,cross_section_table,expected_result",
    [
        (constants.CrossSectionShape.TABULATED_RECTANGLE, "0.04,0.06\n0.1,0.2", 0),
        (constants.CrossSectionShape.TABULATED_RECTANGLE, "0.04,0.06\n0.05,0.2", 1),
        (constants.CrossSectionShape.TABULATED_RECTANGLE, "0.04,0.06\n0.1,0.03", 0),
        (constants.CrossSectionShape.TABULATED_RECTANGLE, "0.04,0.06\n0.1,0.2", 0),
    ],
)
def test_check_cross_section_minimum_diameter_tabulated(
    session, shape, cross_section_table, expected_result
):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
        cross_section_shape=shape,
    )
    check = CrossSectionMinimumDiameterCheck(column=models.CrossSectionLocation.id)
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == expected_result


@pytest.mark.parametrize(
    "shape,width,height,expected_result",
    [
        (
            constants.CrossSectionShape.CLOSED_RECTANGLE,
            "0.1",
            "0.2",
            1,
        ),  # closed rectangle, fail
        (constants.CrossSectionShape.RECTANGLE, "0.1", None, 0),  # open rectangle, pass
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
    factories.CrossSectionLocationFactory(
        cross_section_width=width,
        cross_section_height=height,
        cross_section_shape=shape,
        friction_type=friction_type,
    )
    check = OpenIncreasingCrossSectionConveyanceFrictionCheck(
        column=models.CrossSectionLocation.id
    )
    # this check should pass on cross-section locations which don't use conveyance,
    # regardless of their other parameters
    if not conveyance:
        expected_result = 0
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == expected_result


@pytest.mark.parametrize(
    "cross_section_table,expected_result",
    [
        (
            "0.04,0.06\n0.1,0.2",
            0,
        ),  # open tabulated rectangle, increasing width, pass
        (
            "0.04,0.06\n0.1,0.2\n0.1,0.3",
            0,
        ),  # open tabulated rectangle, equal width segments, pass
        (
            "0.2,0.06\n0.1,0.2",
            1,
        ),  # open tabulated rectangle, decreasing width, fail
        (
            "0.04,0.06\n0.1,0.2\n0,0",
            1,
        ),  # closed tabulated rectangle, fail
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
def test_check_cross_section_increasing_open_with_conveyance_friction_tabulated(
    session, cross_section_table, expected_result, friction_type, conveyance
):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
        cross_section_shape=constants.CrossSectionShape.TABULATED_RECTANGLE,
        friction_type=friction_type,
    )
    check = OpenIncreasingCrossSectionConveyanceFrictionCheck(
        column=models.CrossSectionLocation.id
    )
    # this check should pass on cross-section locations which don't use conveyance,
    # regardless of their other parameters
    if not conveyance:
        expected_result = 0
    invalid_rows = check.get_invalid(session)
    assert len(invalid_rows) == expected_result


@pytest.mark.parametrize("data, result", [["1,2", True], ["1,2,3", False]])
def test_check_correct_lengthtest_check_correct_length(session, data, result):
    factories.CrossSectionLocationFactory(
        cross_section_table="1,0\n2,2\n3,5",
        cross_section_friction_values=data,
    )
    check = CrossSectionVariableCorrectLengthCheck(
        column=models.CrossSectionLocation.cross_section_friction_values
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
    factories.CrossSectionLocationFactory(cross_section_friction_values="0 1")
    check = CrossSectionVariableRangeCheck(
        column=models.CrossSectionLocation.cross_section_friction_values,
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
    factories.CrossSectionLocationFactory(
        cross_section_friction_values="0,1",
        friction_type=constants.FrictionType.MANNING,
    )
    check = CrossSectionVariableFrictionRangeCheck(
        min_value=0,
        max_value=1,
        right_inclusive=False,
        error_code=9999,
        column=models.CrossSectionLocation.cross_section_friction_values,
        friction_types=friction_types,
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


@pytest.mark.parametrize(
    "cross_section_table,result",
    [
        (
            "0.01,0.11\n0.11,0.21",
            True,
        ),  # open tabulated yz, increasing width, pass
        (
            "0.11,0.11\n0.01,0.20",
            False,
        ),  # open tabulated yz, decreasing width, fail
        (
            "0.01,0.11\n0.11,0.21\n0.01,0.11",
            False,
        ),  # closed tabulated yz,  fail
    ],
)
def test_check_cross_section_increasing_open_with_variables(
    session, cross_section_table, result
):
    factories.CrossSectionLocationFactory(
        cross_section_table=cross_section_table,
        cross_section_friction_values="1",
        cross_section_shape=constants.CrossSectionShape.TABULATED_YZ,
    )
    check = OpenIncreasingCrossSectionVariableCheck(
        models.CrossSectionLocation.cross_section_friction_values
    )
    # this check should pass on cross-section locations which don't use conveyance,
    # regardless of their other parameters
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


@pytest.mark.parametrize(
    "shape,width,height,expected",
    [
        (constants.CrossSectionShape.CLOSED_RECTANGLE, 1, 2, (1, 2, "closed")),
        (constants.CrossSectionShape.CLOSED_RECTANGLE, None, None, (0, 0, "closed")),
        (constants.CrossSectionShape.RECTANGLE, 1, 2, (1, 2, "open")),
        (constants.CrossSectionShape.RECTANGLE, None, None, (0, None, "open")),
        (constants.CrossSectionShape.CIRCLE, 1, 2, (1, 1, "closed")),
        (constants.CrossSectionShape.CIRCLE, None, None, (0, 0, "closed")),
        (constants.CrossSectionShape.CIRCLE, None, 2, (0, 0, "closed")),
        (constants.CrossSectionShape.INVERTED_EGG, 1, 2, (1, 1.5, "closed")),
        (constants.CrossSectionShape.EGG, None, None, (0, 0, "closed")),
        (constants.CrossSectionShape.EGG, None, 2, (0, 0, "closed")),
    ],
)
def test_cross_section_configuration_not_tabulated(shape, width, height, expected):
    assert cross_section_configuration_not_tabulated(shape, width, height) == expected


@pytest.mark.parametrize(
    "shape,widths,heights,expected",
    [
        (constants.CrossSectionShape.TABULATED_RECTANGLE, None, None, (0, 0, "closed")),
        (
            constants.CrossSectionShape.TABULATED_TRAPEZIUM,
            [1, 2, 3],
            [1, 2, 4],
            (3, 4, "open"),
        ),
        (
            constants.CrossSectionShape.TABULATED_TRAPEZIUM,
            [1, 2, 0],
            [1, 2, 4],
            (2, 4, "closed"),
        ),
        (
            constants.CrossSectionShape.TABULATED_TRAPEZIUM,
            [1, 2, 3],
            [1, 2, 0],
            (3, 2, "open"),
        ),
        (
            constants.CrossSectionShape.TABULATED_YZ,
            [0, 1, 2, 0],
            [1, 2, 3, 4],
            (2, 3, "open"),
        ),
        (
            constants.CrossSectionShape.TABULATED_YZ,
            [0, 1, 2, 0],
            [0, 2, 3, 0],
            (2, 3, "closed"),
        ),
    ],
)
def test_cross_section_configuration_tabulated(shape, widths, heights, expected):
    assert cross_section_configuration_tabulated(shape, widths, heights) == expected


def test_cross_section_configuration_tabulated_raise():
    with pytest.raises(ValueError):
        cross_section_configuration_tabulated(
            shape=constants.CrossSectionShape.RECTANGLE, widths=None, heights=None
        )


def test_cross_section_configuration_not_tabulated_raise():
    with pytest.raises(ValueError):
        cross_section_configuration_not_tabulated(
            shape=constants.CrossSectionShape.TABULATED_YZ, width=None, height=None
        )


@pytest.mark.parametrize(
    "shape,kwargs, expected",
    [
        (
            constants.CrossSectionShape.TABULATED_YZ,
            {"cross_section_table": "0,1\n1,2\n2,3\n0,4"},
            (2, 3, "open"),
        ),
        (
            constants.CrossSectionShape.CLOSED_RECTANGLE,
            {"cross_section_width": 1, "cross_section_height": 2},
            (1, 2, "closed"),
        ),
    ],
)
def test_cross_section_configuration_for_record(session, shape, kwargs, expected):
    factories.CrossSectionLocationFactory(cross_section_shape=shape, **kwargs)
    check = CrossSectionNullCheck(models.CrossSectionLocation.id)
    records = list(check.to_check(session))
    assert cross_section_configuration_for_record(records[0]) == expected
