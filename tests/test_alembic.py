from alembic import command
from alembic.config import Config
from threedi_modelchecker.threedi_database import ThreediDatabase

import pytest


def test_upgrade(in_memory_sqlite):
    """Tests the migration mechanism on an empty in-memory database"""
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "threedi_modelchecker:migrations")

    with in_memory_sqlite.get_engine().begin() as connection:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    # Test the presence of the v2_connection_nodes table
    assert in_memory_sqlite.get_engine().has_table("v2_connection_nodes")
