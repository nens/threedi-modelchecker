import click
from threedi_schema import ThreediDatabase
from threedi_schema.domain.models import DECLARED_MODELS

from threedi_modelchecker import exporters
from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.config import Config
from threedi_modelchecker.checks.base import CheckLevel


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
def export_checks():
    """Export formatted checks summary to insert in documentation"""
    checks = Config(models=DECLARED_MODELS).checks
    info_checks = []
    warning_checks = []
    error_checks = []
    for check in checks:
        if check.level == CheckLevel.INFO:
            info_checks.append(check)
        elif check.level == CheckLevel.WARNING:
            warning_checks.append(check)
        elif check.level == CheckLevel.ERROR:
            error_checks.append(check)

if __name__ == "__main__":
    check()
