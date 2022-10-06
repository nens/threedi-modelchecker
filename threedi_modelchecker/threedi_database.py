from contextlib import contextmanager
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker

import shutil
import tempfile
import uuid
import warnings


__all__ = ["ThreediDatabase"]


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Switch on legacy_alter_table setting to fix our migrations.

    Why?
    1) SQLite does not support "DROP COLUMN ...". You have to create a new table,
       copy the data, drop the old table, then rename. Luckily Alembic supports this pattern.
       They call it a "batch operation". See https://alembic.sqlalchemy.org/en/latest/batch.html.
    2) Newer SQLite drivers do a lot of fancy checks on a RENAME command. This made our
       "batch operations" fail in case a view referred to the table that is getting a "batch operation".
       The solution was a PRAGMA command. See https://www.sqlite.org/pragma.html#pragma_legacy_alter_table.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA legacy_alter_table=ON")
    # Some additional pragmas recommended in https://www.sqlite.org/security.html, paragraph 1.2
    cursor.execute("PRAGMA cell_size_check=ON")
    cursor.execute("PRAGMA mmap_size=0")
    cursor.close()


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
    try:
        cur.execute("select EnableGpkgAmphibiousMode()")
    except sqlite3.OperationalError:
        pass
    if not found:
        raise RuntimeError("Cannot find any suitable spatialite module")
    cur.close()
    con.enable_load_extension(False)


class ThreediDatabase:
    def __init__(self, connection_settings, db_type=None, echo=False):
        # backwards compat:
        # - connection_settings is just a path, but it could be {"db_path": <path>}
        # - db_type is ignored
        if isinstance(connection_settings, dict):
            self.path = connection_settings["db_path"]
            warnings.warn(
                "'connection-settings' is pending deprecation; please supply a path directly instead",
                UserWarning,
            )
        else:
            self.path = connection_settings
        self.echo = echo

        self._engine = None
        self._base_metadata = None

    @property
    def db_type(self):
        warnings.warn("ThreediDatabase.db_type is pending deprecation", UserWarning)
        return "spatialite"  # backwards compat

    @property
    def settings(self):
        warnings.warn("ThreediDatabase.settings is pending deprecation", UserWarning)
        return {"db_path": self.path}  # backwards compat

    @property
    def engine(self):
        return self.get_engine()

    @property
    def base_path(self):
        return Path(self.path).absolute().parent

    def get_engine(self, get_seperate_engine=False):
        if self._engine is None or get_seperate_engine:
            engine = create_engine("sqlite:///{0}".format(self.path), echo=self.echo)
            listen(engine, "connect", load_spatialite)
            if get_seperate_engine:
                return engine
            else:
                self._engine = engine

        return self._engine

    def get_session(self, **kwargs):
        """Get a SQLAlchemy session for optimal control.

        It is probably necessary to call ``session.commit``, ``session.rollback``
        and/or ``session.close``.

        See also:
          https://docs.sqlalchemy.org/en/13/orm/session_basics.html
        """
        return sessionmaker(bind=self.engine)(**kwargs)

    @contextmanager
    def session_scope(self, **kwargs):
        """Get a session to execute a single transaction in a "with as" block."""
        session = self.get_session(**kwargs)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def file_transaction(self, start_empty=False):
        """Copy the complete database into a tmpdir and work on that one.

        On contextmanager exit, the database is copied back and the real
        database is overwritten. On error, nothing happens.
        """
        with tempfile.TemporaryDirectory() as tempdir:
            work_file = Path(tempdir) / f"work-{uuid.uuid4()}.sqlite"
            # copy the database to the temporary directory
            if not start_empty:
                shutil.copy(self.path, str(work_file))
            # yield a new ThreediDatabase refering to the backup
            try:
                yield self.__class__(str(work_file))
            except Exception as e:
                raise e
            else:
                shutil.copy(str(work_file), self.path)

    def check_connection(self):
        """Check if there a connection can be started with the database

        :return: True if a connection can be established, otherwise raises an
            appropriate error.
        """
        session = self.get_session()
        r = session.execute("select 1")
        return r.fetchone()

    def check_integrity(self):
        """Should be called before doing anything with an untrusted sqlite file."""
        with self.session_scope() as session:
            session.execute("PRAGMA integrity_check")

    def has_table(self, name):
        engine = self.get_engine()
        try:
            # SQLAlchemy >= 1.4
            return inspect(engine).has_table(name)
        except AttributeError:  # SQLAlchemy < 1.4
            return engine.has_table(name)
