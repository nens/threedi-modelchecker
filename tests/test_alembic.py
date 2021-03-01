try:
    from alembic import command
    from alembic.config import Config

    has_alembic = True
except ImportError:
    has_alembic = False

from threedi_modelchecker.threedi_database import ThreediDatabase

import pytest


@pytest.mark.skipif(not has_alembic, reason="Skipping as alembic is not present.")
def test_upgrade():
    """Tests the migration mechanism on an empty in-memory database"""
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "threedi_modelchecker:migrations")
    db = ThreediDatabase({"db_path": ""})

    with db.get_engine().begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    # Test the presence of the v2_connection_nodes table
    connection = db.get_engine().raw_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) from v2_connection_nodes;")
        assert cursor.fetchone() == (0,)
        cursor.close()
    finally:
        connection.close()
