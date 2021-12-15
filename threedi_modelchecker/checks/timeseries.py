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


class TimeseriesIntCheck(BaseCheck):
    """Check that each record in a timeserie starts with an integer"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries

            if not timeserie:
                continue

            for row in timeserie.split():
                elems = row.split(",")
                if len(elems) != 2:
                    continue  # checked elsewhere

                try:
                    int(elems[0].strip())
                except ValueError:
                    invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return f"{self.column_name} contains an invalid timestep, expected an integer"


class TimeseriesFloatCheck(BaseCheck):
    """Check that each record in a timeserie ends with a float"""

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries

            if not timeserie:
                continue

            for row in timeserie.split():
                elems = row.split(",")
                if len(elems) != 2:
                    continue  # checked elsewhere

                try:
                    float(elems[1].strip())
                except ValueError:
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


class TimeseriesMaxLengthCheck(BaseCheck):
    """The timesteps in a timeseries should increase"""

    def __init__(self, max_length, *args, **kwargs):
        self.max_length = max_length
        super().__init__(*args, **kwargs)

    def get_invalid(self, session):
        invalid_timeseries = []

        for row in self.to_check(session).all():
            timeserie = row.timeseries
            try:
                timesteps = [x[0] for x in parse_timeseries(timeserie)]
            except (ValueError, TypeError):
                continue  # other checks will catch these

            if len(timesteps) > self.max_length:
                invalid_timeseries.append(row)

        return invalid_timeseries

    def description(self):
        return f"{self.column_name} should not contain more than {self.max_length} timesteps"
