import pytest
from threedi_schema import models

from threedi_modelchecker.checks.timeseries import (
    TimeseriesIncreasingCheck,
    TimeseriesRowCheck,
    TimeseriesStartsAtZeroCheck,
    TimeseriesTimestepCheck,
    TimeseriesValueCheck,
)

from .factories import BoundaryConditions2DFactory


@pytest.mark.parametrize(
    "timeseries", ["0,-0.5", "0,-0.5 \n59,-0.5\n60,-0.5\n   ", "", None]
)
def test_timeseries_row_check_ok(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesRowCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


@pytest.mark.parametrize("timeseries", ["0,-0.5,14"])
def test_timeseries_row_check_error(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesRowCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1


# Note: Invalid rows are 'valid' for this check
@pytest.mark.parametrize(
    "timeseries", ["0,foo", "0,-0.5\n59,-0.5\n60,-0.5", "0,-0.5,14", "", None]
)
def test_timeseries_timestep_check_ok(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesTimestepCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


@pytest.mark.parametrize("timeseries", ["foo,9.1", "-1, 1.0"])
def test_timeseries_timestep_check_error(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesTimestepCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1


# Note: Invalid rows are 'valid' for this check
@pytest.mark.parametrize(
    "timeseries",
    [
        "foo,2.1",
        "foo,1E5",
        "foo,-2",
        "0,-0.5 \n59,-0.5\n 60,-0.5\n   ",
        "0,-0.5,14",
        "0,-0.5,14",
        "",
        None,
    ],
)
def test_timeseries_value_check_ok(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesValueCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


@pytest.mark.parametrize("timeseries", ["1,foo", "1,nan", "1,inf"])
def test_timeseries_value_check_error(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesValueCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1


@pytest.mark.parametrize(
    "timeseries",
    [
        "0,2.1",
        "0,-0.5 \n59, -0.5\n60 ,-0.5\n   ",
        "0,-0.5,14",
        "0,-0.5,14",
        "foo,1.2",
        "1,foo",
        "",
        None,
    ],
)
def test_timeseries_increasing_check_ok(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesIncreasingCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


@pytest.mark.parametrize("timeseries", ["2,1.0\n2,1.0", "2,1.0\n1,1.0\n2,1.0"])
def test_timeseries_increasing_check_error(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesIncreasingCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1


@pytest.mark.parametrize(
    "timeseries",
    [
        "0,2.1",
        "0,2.1\n1,4.2",
        "0,2.1\n-1,4.2",
        "0,-0.5 \n59, -0.5\n60 ,-0.5\n   ",
        "0,-0.5,14",
        "0,-0.5,14",
        "foo,1.2",
        "1,foo",
        "",
        None,
    ],
)
def test_timeseries_starts_zero_check_ok(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesStartsAtZeroCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


@pytest.mark.parametrize("timeseries", ["2,1.0", "2,1.0\n3,1.0"])
def test_timeseries_starts_zero_check_err(session, timeseries):
    BoundaryConditions2DFactory(timeseries=timeseries)

    check = TimeseriesStartsAtZeroCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1
