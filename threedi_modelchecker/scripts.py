import csv
from io import StringIO

import click
from threedi_schema import ThreediDatabase
from threedi_schema.domain.models import DECLARED_MODELS

from threedi_modelchecker import exporters
from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.config import Config
from threedi_modelchecker.model_checks import ThreediModelChecker


@click.group()
def cli():
    pass


@cli.command()
@click.option("-f", "--file", help="Write errors to file, instead of stdout")
@click.option(
    "-l",
    "--level",
    type=click.Choice([x.name for x in CheckLevel], case_sensitive=False),
    default="ERROR",
    help="Minimum check level.",
)
@click.option(
    "-s",
    "--sqlite",
    type=click.Path(exists=True, readable=True),
    help="Path to an sqlite (spatialite) file",
    required=True,
)
def check(sqlite, file, level):
    """Checks the threedi-model for errors / warnings / info messages"""
    db = ThreediDatabase(sqlite, echo=False)
    """Checks the threedi model schematisation for errors."""
    level = level.upper()
    if level == "ERROR":
        msg = "errors"
    elif level == "WARNING":
        msg = "errors or warnings"
    else:
        msg = "errors, warnings or info messages"
    click.echo("Parsing schematisation for any %s" % msg)
    if file:
        click.echo("Model errors will be written to %s" % file)

    mc = ThreediModelChecker(db)
    model_errors = mc.errors(level=level)

    if file:
        exporters.export_to_file(model_errors, file)
    else:
        exporters.print_errors(model_errors)

    click.echo("Finished processing model")


@cli.command()
@click.option("-f", "--file", help="Write output to file, instead of stdout")
@click.option(
    "-ft",
    "--format",
    type=click.Choice(["rst", "csv"], case_sensitive=False),
    default="rst",
    help="Export format for checks table",
)
def export_checks(file, format):
    """Export formatted checks summary to insert in documentation or use elsewhere"""

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
        for check in checks:
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

        for check in checks:
            writer.writerow(
                {
                    "error_code": check.error_code,
                    "level": check.level.name,
                    "description": check.description(),
                }
            )

        return output_buffer.getvalue()

    checks = Config(models=DECLARED_MODELS).checks

    if format.lower() == "rst":
        table = generate_rst_table(checks=checks)
    elif format.lower() == "csv":
        table = generate_csv_table(checks=checks)
    if file:
        with open(file, "w") as f:
            f.write(table)
    else:
        click.echo(table)


if __name__ == "__main__":
    check()
