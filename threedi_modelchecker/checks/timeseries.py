from sqlalchemy import func
from threedi_schema import models

from .base import BaseCheck


def parse_timeseries(timeseries_str):
    if not timeseries_str:
        return []
    output = []
    for line in timeseries_str.split():
        timestep, value = line.split(",")
        timestep = int(timestep.strip())
        output.append([timestep, float(value.strip())])
    return output


def compare_timesteps(first_timeseries: str, second_timeseries: str) -> bool:
    first_timesteps = [pair[0] for pair in parse_timeseries(first_timeseries)]
    second_timesteps = [pair[0] for pair in parse_timeseries(second_timeseries)]
    return first_timesteps == second_timesteps


class TimeseriesExistenceCheck(BaseCheck):
    """Check that an empty timeseries has not been provided."""

    def get_invalid(self, session):
        invalid_rows = []
        for row in self.to_check(session).all():
            # this will catch False, None, "", and any other falsy value
            if not row.timeseries:
                invalid_rows.append(row)

        return invalid_rows

    def description(self):
        return f"{self.column_name} contains an empty timeseries; remove the {self.table.name} instance or provide valid timeseries."


class TimeSeriesEqualTimestepsCheck(BaseCheck):
    """
    Check that the timesteps in all timeseries in a column are equal.

    This checks the timesteps for all timeseries in a column against the timesteps in the first
    timeseries in that column. Consequently, if the first timeseries is wrong, all the other timeseries
    in that column will raise a warning.
    This check does not compare timeseries between different columns; for that, FirstTimeSeriesEqualTimestepsCheck
    is used.
    """

    def get_invalid(self, session):
        invalid_timeseries = []

        first_timeseries = None

        for row in self.to_check(session).all():
            timeseries = row.timeseries

            if not timeseries:
                continue

            if not first_timeseries:
                first_timeseries = timeseries
                continue  # don't compare first timeseries with itself

            try:
                if not compare_timesteps(
                    first_timeseries=first_timeseries,
                    second_timeseries=timeseries,
                ):
                    invalid_timeseries.append(row)
            except Exception:  # other checks will catch these
                pass

        return invalid_timeseries

    def description(self):
        return (
            f"One or more timesteps in {self.column_name} did not match the timesteps in the first timeseries in the column."
            + "The timesteps in all timeseries must be the same."
        )


class FirstTimeSeriesEqualTimestepsCheck(BaseCheck):
    """
    Check that the timesteps in the first timeseries in the boundary condition columns are equal, if they both exist.

    This is used in conjunction with TimeSeriesEqualTimestepsCheck to confirm that the timeseries in all the boundary
    conditions have the same timesteps. If each timeseries within each column has the same timesteps, and the first
    timeseries of each column matches timesteps with the first timeseries of each other column, then the timesteps of
    all the timeseries must be the same.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.BoundaryCondition1D.timeseries, *args, **kwargs)

    def get_invalid(self, session):
        invalid_timeseries = []

        first_1d_timeseries = (
            session.query(models.BoundaryCondition1D.timeseries.table)
            .order_by(models.BoundaryCondition1D.id)
            .limit(1)
            .all()
        )

        first_2d_timeseries = (
            session.query(models.BoundaryConditions2D.timeseries.table)
            .order_by(models.BoundaryConditions2D.id)
            .limit(1)
            .all()
        )

        if first_1d_timeseries and first_2d_timeseries:
            try:
                if not compare_timesteps(
                    first_timeseries=first_1d_timeseries[0].timeseries,
                    second_timeseries=first_2d_timeseries[0].timeseries,
                ):
                    invalid_timeseries.append(first_1d_timeseries[0])
            except Exception:  # other checks will catch these
                pass

        return invalid_timeseries

    def description(self):
        return (
            "The timesteps for the first boundary_condition_1d.timeseries did not match the timesteps for the first boundary_condition_2d.timeseries. "
            + "All boundary conditions must have the same timesteps in their timeseries."
        )


class TimeseriesRowCheck(BaseCheck):
    """Check that each record in a timeserie contains 2 elements"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries

            if not timeserie:
                continue

            if any(len(x.split(",")) != 2 for x in timeserie.split()):
                invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return (
            f"{self.column_name} must contain 2 elements per line separated by a comma"
        )


class TimeseriesTimestepCheck(BaseCheck):
    """Check that each record in a timeserie starts with an integer >= 0"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries

            if not timeserie:
                continue

            for timeseries_row in timeserie.split():
                elems = timeseries_row.split(",")
                if len(elems) != 2:
                    continue  # checked elsewhere

                try:
                    timestep = int(elems[0].strip())
                except ValueError:
                    invalid_timeseries.append(row)
                    continue

                if timestep < 0:
                    invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return (
            f"{self.column_name} contains an invalid timestep, expected an integer >= 0"
        )


class TimeseriesValueCheck(BaseCheck):
    """Check that each record in a timeserie ends with a float and is not an invalid or empty string"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries

            if not timeserie:
                continue

            for timeseries_row in timeserie.split():
                elems = timeseries_row.split(",")
                if len(elems) != 2:
                    continue  # checked elsewhere

                try:
                    value = float(elems[1].strip())
                except ValueError:
                    invalid_timeseries.append(row)
                    continue

                if str(value) in {"nan", "inf", "-inf"}:
                    invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return f"{self.column_name} contains an invalid value, expected a float"


class TimeseriesIncreasingCheck(BaseCheck):
    """The timesteps in a timeseries should increase"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries
            try:
                timesteps = [x[0] for x in parse_timeseries(timeserie)]
            except (ValueError, TypeError):
                continue  # other checks will catch these

            if len(timesteps) < 2:
                continue

            if not all(b > a for (a, b) in zip(timesteps[:-1], timesteps[1:])):
                invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return f"{self.column_name} should be monotonically increasing"


class TimeseriesStartsAtZeroCheck(BaseCheck):
    """The timesteps in a timeseries should start at 0"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries
            try:
                timesteps = [x[0] for x in parse_timeseries(timeserie)]
            except (ValueError, TypeError):
                continue  # other checks will catch these

            if len(timesteps) == 0:
                continue

            if timesteps[0] != 0:
                invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return f"{self.column_name} should be start at timestamp 0"


class TimeUnitsValidCheck(BaseCheck):
    """Check that an empty timeseries has not been provided."""

    def get_invalid(self, session):
        valid_units = [
            "second",
            "seconds",
            "sec",
            "s",
            "minute",
            "minutes",
            "min",
            "m",
            "hour",
            "hours",
            "hr",
            "h",
        ]
        return (
            self.to_check(session)
            .filter(func.lower(self.column).not_in(valid_units))
            .all()
        )

    def description(self):
        return f"{self.column_name} is not recognized as a valid unit of time."


class TimeUnitsEqualCheck(BaseCheck):
    """
    Check that all time_units values within a single table are identical.

    This checks the time_units for all records in a column against the time_units in the first
    record in that column. Consequently, all records in that column must have the same time_units.
    This check does not compare time_units between different tables; for that, FirstTimeUnitsEqualCheck
    is used.
    """

    def get_invalid(self, session):
        invalid_records = []

        first_time_units = None

        for row in self.to_check(session).all():
            time_units = row.time_units

            if not time_units:
                continue

            if not first_time_units:
                first_time_units = time_units
                continue  # don't compare first record with itself

            if time_units.lower() != first_time_units.lower():
                invalid_records.append(row)

        return invalid_records

    def description(self):
        return (
            f"One or more records in {self.column_name} have a different time_units than the first record. "
            + "All time_units within this table must be identical."
        )


class FirstTimeUnitsEqualCheck(BaseCheck):
    """
    Check that the first time_units value is identical across all boundary condition tables.

    This is used in conjunction with TimeUnitsEqualCheck to confirm that all time_units across
    all boundary condition tables are identical. If each time_units within each table is identical,
    and the first time_units of each table matches with the first time_units of each other table,
    then all time_units must be identical across all tables.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(column=models.BoundaryCondition1D.time_units, *args, **kwargs)

    def get_invalid(self, session):
        first_1d = (
            session.query(models.BoundaryCondition1D)
            .order_by(models.BoundaryCondition1D.id)
            .first()
        )
        first_2d = (
            session.query(models.BoundaryConditions2D)
            .order_by(models.BoundaryConditions2D.id)
            .first()
        )
        if first_1d and first_2d:
            if first_1d.time_units.lower() != first_2d.time_units.lower():
                return [first_1d]

        return []

    def description(self):
        return (
            "The value for the first boundary_condition_1d.time_units did not match the value for the first boundary_condition_2d.time_units. "
            + "All boundary conditions must have the same time units."
        )
