Threedi-modelchecker
====================

.. image:: https://img.shields.io/pypi/v/threedi-modelchecker.svg
        :target: https://pypi.org/project/threedi-modelchecker/

.. image:: https://travis-ci.com/nens/threedi-modelchecker.svg?branch=master
    :target: https://travis-ci.com/nens/threedi-modelchecker

Threedi-modelchecker is a tool to verify the correctness of a 3Di model.
The goal is to provide a tool for model builders to quickly check if his/her 
model is correct and can run a 3Di simulation. It provides detailed 
information about any potential errors in the model.

Threedi-modelchecks works with both spatialite and postgis databases. However, 
the database should always have the latest 3Di migration: https://docs.3di.lizard.net/en/stable/d_before_you_begin.html#database-overview 

Installation:

    pip install threedi-modelchecker


Threedi-modelchecker is also integrated into the ThreediToolbox Qgis plugin: https://github.com/nens/ThreeDiToolbox


Example
-------

The following code sample shows how you can use the modelchecker to run all configured
checks and print an overview of all discovered errors::

    from threedi_modelchecker.exporters import format_check_results
    from threedi_modelchecker.model_checks import ThreediModelChecker
    from threedi_modelchecker.threedi_database import ThreediDatabase

    sqlite_file = "<Path to your sqlite file>"
    database = ThreediDatabase(
        connection_settings={"db_path": sqlite_file}, db_type="spatialite"
    )

    model_checker = ThreediModelChecker(database)
    for check, error in model_checker.errors():
        print(format_check_results(check, error))


Development
-----------

A docker image has been created for easy development. It contains an postgis 
server with an empty 3Di database to allow for easy testing.

Build the image:

    docker-compose build

Run the tests:

    docker-compose run modelchecker pytest

Release
-------

Make sure you have zestreleaser_ installed.

    fullrelease

When you create a tag on git, Travis CI automatically creates a new release to pypi_.

.. _zestreleaser: https://zestreleaser.readthedocs.io/en/latest/
.. _pypi: https://pypi.org/project/threedi-modelchecker/
