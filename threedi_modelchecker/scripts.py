from threedi_modelchecker import exporters
from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.threedi_database import ThreediDatabase

import click


@click.group()
@click.option("-f", "--file", help="Write errors to file, instead of stdout")
@click.option(
    "-l",
    "--level",
    type=click.Choice([x.name for x in CheckLevel], case_sensitive=False),
    default="ERROR",
    help="Minimum check level.",
)
@click.pass_context
def check_model(ctx, file, level):
    """Checks the threedi-model for errors / warnings / info messages"""
    level = level.upper()
    if level == "ERROR":
        msg = "errors"
    elif level == "WARNING":
        msg = "errors or warnings"
    else:
        msg = "errors, warnings or info messages"
    click.echo("Parsing threedi-model for any %s" % msg)
    if file:
        click.echo("Model errors will be written to %s" % file)


@check_model.command()
@click.option("-d", "--database", required=True, help="database name to connect to")
@click.option("-h", "--host", required=True, help="database server host")
@click.option("-p", "--port", required=True, default=5432, help="database server port")
@click.option("-u", "--username", required=True, help="database username")
@click.pass_context
def postgis(context, database, host, port, username, password):
    """Parse a postgis model"""
    postgis_settings = {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
    }
    db = ThreediDatabase(
        connection_settings=postgis_settings, db_type="postgres", echo=False
    )
    process(db, context.parent)


@check_model.command()
@click.option(
    "-s",
    "--sqlite",
    required=True,
    type=click.Path(exists=True, readable=True),
    help="sqlite file",
)
@click.pass_context
def sqlite(context, sqlite):
    """Parse a sqlite model"""
    sqlite_settings = {"db_path": sqlite, "db_file": sqlite}
    db = ThreediDatabase(
        connection_settings=sqlite_settings, db_type="spatialite", echo=False
    )
    process(db, context.parent)


def process(threedi_db, context):
    mc = ThreediModelChecker(threedi_db)
    model_errors = mc.errors(level=context.params.get("level"))

    file_output = context.params.get("file")
    if file_output:
        exporters.export_to_file(model_errors, file_output)
    else:
        exporters.print_errors(model_errors)

    click.echo("Finished processing model")


if __name__ == "__main__":
    exit(check_model())
