from sqlalchemy import select
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
    Check that the timesteps in all boundary condition timeseries are equal.

    This checks the timesteps for all timeseries against the timesteps in the first 1D boundary
    condition timeseries, or if that doesn't exist, the first 2D boundary condition timeseries.
    Consequently, if the first timeseries is wrong, all the other boundary conditions will raise
    give a warning.
    """

    def compare_timesteps(self, first_timeseries: str, second_timeseries: str) -> bool:
        first_timesteps = [pair[0] for pair in parse_timeseries(first_timeseries)]
        second_timesteps = [pair[0] for pair in parse_timeseries(second_timeseries)]
        return first_timesteps == second_timesteps

    def get_invalid(self, session):
        invalid_timeseries = []

        # set the first timeseries variable to None if the timeseries column is empty
        # using a walrus operator avoids running the query both for checking emptiness and for fetching the value
        first_1d_timeseries = (
            timeseries_query[0][0]
            if (
                timeseries_query := session.execute(
                    select(models.BoundaryCondition1D.timeseries)
                    .order_by(models.BoundaryCondition1D.id)
                    .limit(1)
                ).all()
            )
            else None
        )

        first_2d_timeseries = (
            timeseries_query[0][0]
            if (
                timeseries_query := session.execute(
                    select(models.BoundaryConditions2D.timeseries)
                    .order_by(models.BoundaryConditions2D.id)
                    .limit(1)
                ).all()
            )
            else None
        )

        # if both the 1d and 2d boundary conditions are empty there are no timeseries, so also no nonmatching ones
        if not first_1d_timeseries and not first_2d_timeseries:
            return []

        # use to properly format the error description
        self.one_d_timeseries_used = True if first_1d_timeseries else False

        for row in self.to_check(session).all():
            timeseries = row.timeseries

            if not timeseries:
                continue

            if not self.compare_timesteps(
                first_timeseries=(
                    first_1d_timeseries if first_1d_timeseries else first_2d_timeseries
                ),
                second_timeseries=timeseries,
            ):
                invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return (
            f"One or more timesteps in {self.column_name} did not match the first timeseries in this "
            + f"models.BoundaryCondition{'1D' if self.one_d_timeseries_used else 's2D'}.timeseries. "
            + "The timesteps in all timeseries must be the same."
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
