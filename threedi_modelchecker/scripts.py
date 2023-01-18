import click
from threedi_schema import ThreediDatabase

from threedi_modelchecker import exporters
from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.model_checks import ThreediModelChecker


@click.group()
@click.option(
    "-s",
    "--sqlite",
    type=click.Path(exists=True, readable=True),
    help="Path to an sqlite (spatialite) file",
    required=True,
)
@click.pass_context
def main(ctx, sqlite):
    """Checks the threedi-model for errors / warnings / info messages"""
    ctx.ensure_object(dict)

    db = ThreediDatabase(sqlite, echo=False)
    ctx.obj["db"] = db


@main.command()
@click.option("-f", "--file", help="Write errors to file, instead of stdout")
@click.option(
    "-l",
    "--level",
    type=click.Choice([x.name for x in CheckLevel], case_sensitive=False),
    default="ERROR",
    help="Minimum check level.",
)
@click.pass_context
def check(ctx, file, level):
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

    mc = ThreediModelChecker(ctx.obj["db"])
    model_errors = mc.errors(level=level)

    if file:
        exporters.export_to_file(model_errors, file)
    else:
        exporters.print_errors(model_errors)

    click.echo("Finished processing model")


if __name__ == "__main__":
    main()
