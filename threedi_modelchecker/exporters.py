import csv
from collections import namedtuple
from io import StringIO
from typing import Iterator, NamedTuple, Tuple

from geoalchemy2.elements import WKBElement

from threedi_modelchecker.checks.base import BaseCheck

ErrorWithGeom = namedtuple(
    "ErrorWithGeom",
    ["name", "code", "id", "table", "column", "value", "description", "geom"],
)


# error handling export functions
def print_errors(errors):
    """Simply prints all errors to stdout

    :param errors: iterator of BaseModelError
    """
    for error in errors:
        print(format_check_results(*error))


def export_to_file(errors, file):
    """Write errors to a new file, separated with newlines.

    File cannot be an already existing file.

    :param errors: iterator of BaseModelError
    :param file:
    :return: None
    :raise FileExistsError: if the file already exists
    """
    with open(file, "w") as f:
        for error in errors:
            f.write(format_check_results(*error) + "\n")


def export_with_geom(
    errors: Iterator[Tuple[BaseCheck, NamedTuple]],
) -> list[ErrorWithGeom]:
    """Process errors into a list that includes the geometry related to the error

    :param errors: iterator of BaseModelError
    :return: A list of ErrorWithGeom named tuples, each containing details about the error,
    including geometry if available
    """
    errors_with_geom = []
    for check, error_row in errors:
        geom = None
        if hasattr(error_row, "geom") and isinstance(error_row.geom, WKBElement):
            geom = error_row.geom
        errors_with_geom.append(
            ErrorWithGeom(
                name=check.level.name,
                code=check.error_code,
                id=error_row.id,
                table=check.table.name,
                column=check.column.name,
                value=getattr(error_row, check.column.name),
                description=check.description(),
                geom=geom,
            )
        )
    return errors_with_geom


def format_check_results(check: BaseCheck, invalid_row: NamedTuple):
    OUTPUT_FORMAT = "{level}{error_code:04d} (id={row_id:d}) {description!s}"
    return OUTPUT_FORMAT.format(
        level=check.level.name[:1],
        error_code=check.error_code,
        row_id=invalid_row.id,
        description=check.description(),
    )


# check overview export functions
def order_checks(checks) -> list:
    """
    Alphabetically order checks so that they will consistently be ordered the same.
    This orders first by error code, and then checks with the same error code are
    sorted alphabetically by description. Checks are not sorted by level, because
    in general, checks with the same error code have the same level.

    This makes Github PR requests a lot clearer.
    """
    return sorted(checks, key=lambda k: (k.error_code, k.description()))


def generate_rst_table(checks) -> str:
    "Generate an RST table to copy into the Sphinx docs with a list of checks"
    rst_table_string = ""
    header = (
        ".. list-table:: Executed checks\n"
        + "   :widths: 10 20 40\n"
        + "   :header-rows: 1\n\n"
        + "   * - Check number\n"
        + "     - Check level\n"
        + "     - Check message"
    )
    rst_table_string += header
    for check in order_checks(checks):
        # pad error code with leading zeroes so it is always 4 numbers
        formatted_error_code = str(check.error_code).zfill(4)
        check_row = (
            "\n"
            + f"   * - {formatted_error_code}\n"
            + f"     - {check.level.name.capitalize()}\n"
            + f"     - {check.description()}"
        )
        rst_table_string += check_row
    return rst_table_string


def generate_csv_table(checks) -> str:
    "Generate an CSV table with a list of checks for use elsewhere"
    # a StringIO buffer is used so that the CSV can be printed to terminal as well as written to file
    output_buffer = StringIO()
    fieldnames = ["error_code", "level", "description"]
    writer = csv.DictWriter(
        output_buffer, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC
    )

    writer.writeheader()

    checks = order_checks(checks)

    for check in checks:
        writer.writerow(
            {
                "error_code": check.error_code,
                "level": check.level.name,
                "description": check.description(),
            }
        )

    return output_buffer.getvalue()
