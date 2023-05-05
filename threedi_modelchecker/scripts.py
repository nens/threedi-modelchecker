import re

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
@click.option(
    "--allow-beta",
    is_flag=True,
    default=False,
    help="Don't check whether beta features were used in the database.",
)
@click.option(
    "--ignore-checks",
    type=str,
    help="Regex pattern; check codes matching this pattern are ignored.",
    default=None,
)
def check(sqlite, file, level, allow_beta, ignore_checks):
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
    if ignore_checks:
        ignore_checks = re.compile(ignore_checks)

    mc = ThreediModelChecker(threedi_db=db, allow_beta_features=allow_beta)
    model_errors = mc.errors(level=level, ignore_checks=ignore_checks)

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
    checks = Config(models=DECLARED_MODELS).checks

    if format.lower() == "rst":
        table = exporters.generate_rst_table(checks=checks)
    elif format.lower() == "csv":
        table = exporters.generate_csv_table(checks=checks)
    if file:
        with open(file, "w") as f:
            f.write(table)
    else:
        click.echo(table)


if __name__ == "__main__":
    check()
