import click

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.exporters import print_errors, export_to_file


# TODO: --file option currently does nothing!
@click.group()
@click.option('-f', '--file', help='Write errors to file, instead of stdout')
def check_model(file):
    """Checks the threedi-model for errors"""
    click.echo('Parsing threedi-model for any errors')
    if file:
        click.echo('Errors will be written to %s' % file)


@check_model.command()
@click.option('-d', '--database', required=True, help='database name to connect to')
@click.option('-h', '--host', required=True, help='database server host')
@click.option('-p', '--port', required=True, default=5432, help='database server port')
@click.option('-u', '--username', required=True, help='database username')
def postgis(database, host, port, username, password):
    """Parse a postgis model"""
    postgis_settings = {
        'host': host,
        'port': port,
        'database': database,
        'username': username,
        'password': password
    }
    db = ThreediDatabase(
        connection_settings=postgis_settings,
        db_type='postgres',
        echo=False
    )
    mc = ThreediModelChecker(db)
    model_errors = mc.parse_model()
    print_errors(model_errors)
    print('done')


@check_model.command()
@click.option('-s', '--sqlite', required=True,
              type=click.Path(exists=True, readable=True),
              help='sqlite file')
def sqlite(sqlite):
    """Parse a sqlite model"""
    sqlite_settings = {
        'db_path': sqlite,
        'db_file': sqlite
    }
    db = ThreediDatabase(
        connection_settings=sqlite_settings,
        db_type='spatialite',
        echo=False
    )
    mc = ThreediModelChecker(db)
    model_errors = mc.parse_model()
    print_errors(model_errors)
    print('done')


if __name__ == '__main__':
    exit(check_model())
