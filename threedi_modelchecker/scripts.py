from threedi_modelchecker import exporters
from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.schema import ModelSchema
from threedi_modelchecker.threedi_database import ThreediDatabase

import click


@click.group()
@click.option(
    "-s",
    "--sqlite",
    type=click.Path(exists=True, readable=True),
    help="Path to an sqlite (spatialite) file",
    required=True,
)
@click.pass_context
def threedi_modelchecker(ctx, sqlite):
    """Checks the threedi-model for errors / warnings / info messages"""
    ctx.ensure_object(dict)

    db = ThreediDatabase(sqlite, echo=False)
    ctx.obj["db"] = db


@threedi_modelchecker.command()
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


@threedi_modelchecker.command()
@click.option(
    "-r", "--revision", default="head", help="The schema revision to migrate to"
)
@click.option("--backup/--no-backup", default=True)
@click.option("--set-views/--no-set-views", default=True)
@click.option(
    "--upgrade-spatialite-version/--no-upgrade-spatialite-version", default=False
)
@click.pass_context
def migrate(ctx, revision, backup, set_views, upgrade_spatialite_version):
    """Migrate the threedi model schematisation to the latest version."""
    schema = ModelSchema(ctx.obj["db"])
    click.echo("The current schema revision is: %s" % schema.get_version())
    click.echo("Running alembic upgrade script...")
    schema.upgrade(
        revision=revision,
        backup=backup,
        set_views=set_views,
        upgrade_spatialite_version=upgrade_spatialite_version,
    )
    click.echo("The migrated schema revision is: %s" % schema.get_version())


@threedi_modelchecker.command()
@click.pass_context
def index(ctx):
    """Set the indexes of a threedi model schematisation."""
    schema = ModelSchema(ctx.obj["db"])
    click.echo("Recovering indexes...")
    schema.set_spatial_indexes()
    click.echo("Done.")


if __name__ == "__main__":
    threedi_modelchecker()
