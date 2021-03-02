Creating revisions
==================

For each change in the 3Di model schematisation, a revision must be created
that is able to move a given database forward to the current schematisation.

We use Alembic for managing these revisions. See https://alembic.sqlalchemy.org.

In short, create an empty revision file as follows::

    $ alembic revision -m "create new table" --rev-id=0205

Or, autogenerate a candidate revision file based on a change in the schema
definition and a database that is in the latest revision state::

    $ alembic revision -m --autogenerate "create new table" --rev-id=0205


Note that we fix revision IDs to integers (padded with zeros). Before creating,
check the latest revision number, add one, pad with zeros, and include it
in the command using the ``--rev-id`` argument.

Also, note that with SQLite you should use "batch mode", read more at 
https://alembic.sqlalchemy.org/en/latest/batch.html
