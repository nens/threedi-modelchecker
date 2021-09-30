from alembic import context
from threedi_modelchecker.threedi_model.models import Base
from sqlalchemy import engine_from_config
from sqlalchemy import pool

target_metadata = Base.metadata
config = context.config


def run_migrations_online():
    """Run migrations in 'online' mode.

    Note: SQLite does not (completely) support transactions, so, backup the
    SQLite before running migrations.
    """
    connectable = config.attributes.get("connection")
    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise ValueError("Offline mode is not supported")
else:
    run_migrations_online()
