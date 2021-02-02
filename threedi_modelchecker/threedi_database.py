from datetime import datetime

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.sql import select, func
from sqlalchemy.event import listen

from threedi_modelchecker.threedi_model import constants
from threedi_modelchecker.threedi_model.models import Base, SouthMigrationHistory


def load_spatialite(con, connection_record):
    """Load spatialite extension as described in
    https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html"""
    import sqlite3

    con.enable_load_extension(True)
    cur = con.cursor()
    libs = [
        # SpatiaLite >= 4.2 and Sqlite >= 3.7.17, should work on all platforms
        ("mod_spatialite", "sqlite3_modspatialite_init"),
        # SpatiaLite >= 4.2 and Sqlite < 3.7.17 (Travis)
        ("mod_spatialite.so", "sqlite3_modspatialite_init"),
        # SpatiaLite < 4.2 (linux)
        ("libspatialite.so", "sqlite3_extension_init"),
    ]
    found = False
    for lib, entry_point in libs:
        try:
            cur.execute("select load_extension('{}', '{}')".format(lib, entry_point))
        except sqlite3.OperationalError:
            continue
        else:
            found = True
            break
    if not found:
        raise RuntimeError("Cannot find any suitable spatialite module")
    cur.close()
    con.enable_load_extension(False)


class ThreediDatabase:

    def __init__(self, engine: Engine):
        self.engine = engine
        if self.engine.dialect.name == 'sqlite':
            listen(engine, "connect", load_spatialite)

    @classmethod
    def spatialite(cls, file, *args, **kwargs):
        """Helper method to create a spatialite ThreediDatabase"""
        engine = create_engine(f"sqlite:///{file}", *args, **kwargs)
        return cls(engine)

    @classmethod
    def postgis(cls, host, port, database, username, password, *args, **kwargs):
        """Helper method to create a postgis ThreediDatabase"""
        engine = create_engine(
            f"postgresql://{username}:{password}@{host}:{port}/{database}", *args, **kwargs)
        return cls(engine)

    def session(self, **kwargs) -> Session:
        return sessionmaker(bind=self.engine, **kwargs)()

    def create_schema(self):
        """Create all tables required for a 3di model"""
        if self.engine.dialect.name == 'sqlite':
            conn = self.engine.connect()
            conn.execute(select([func.InitSpatialMetaData()]))
        Base.metadata.create_all(self.engine)

        migration = SouthMigrationHistory(
            id=constants.LATEST_MIGRATION_ID,
            app_name='threedi_tools',
            migration=constants.LATEST_MIGRATION_NAME,
            applied=datetime.now()
        )
        session = self.session()
        session.add(migration)
        session.commit()

    def check_connection(self) -> Connection:
        """Try to connect to the databse and return a Connection an success"""
        return self.engine.connect()
