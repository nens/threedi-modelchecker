Threedi-modelchecker
====================

.. image:: https://img.shields.io/pypi/v/threedi-modelchecker.svg
        :target: https://pypi.org/project/threedi-modelchecker/

.. Github Actions status — https://github.com/nens/threedi-modelchecker/actions

.. image:: https://github.com/nens/threedi-modelchecker/actions/workflows/test.yml/badge.svg
	:alt: Github Actions status
	:target: https://github.com/nens/threedi-modelchecker/actions/workflows/test.yml


Threedi-modelchecker is a tool to verify the correctness of a 3Di schematisation.
The goal is to provide a tool for builders to quickly check if his/her 
schematisation is correct and can be converted to a 3Di-Model to run a 3Di simulation. It provides detailed 
information about any potential errors in the schematisation.

Threedi-modelchecks only work against the latest 3Di migration: https://docs.3di.lizard.net/en/stable/d_before_you_begin.html#database-overview 

Note:

In 2021 we changed the naming within the 3Di realm. To better understand what users meant with 'model' we made a clear distinction between a schematisation and a model. A schematisation is build interactively by the user and this schematisation will be converted to a 3Di-Model which can be used in simulations. This repo is still called the threedi-modelchecker which might lead to confusion.

Installation::

    pip install threedi-modelchecker


Threedi-modelchecker is also integrated into the ThreediToolbox Qgis plugin: https://github.com/nens/ThreeDiToolbox


Example
-------

The following code sample shows how you can use the modelchecker to run all configured
checks and print an overview of all discovered errors::

    from threedi_modelchecker.exporters import format_check_results
    from threedi_modelchecker import ThreediModelChecker
    from threedi_modelchecker import ThreediDatabase

    sqlite_file = "<Path to your sqlite file>"
    database = ThreediDatabase(sqlite_file)

    model_checker = ThreediModelChecker(database)
    for check, error in model_checker.errors(level="WARNING"):
        print(format_check_results(check, error))


Command-line interface
----------------------

Use the modelchecker from the command line as follows::

    threedi_modelchecker -s path/to/model.sqlite check -l warning 

By default, WARNING and INFO checks are ignored.


Migrations
----------

Migrate the schematisation file to the latest version as follows::

    threedi_modelchecker -s path/to/model.sqlite migrate

The file will be change in-place.


Development
-----------

A docker image has been created for easy development. It contains an postgis 
server with an empty 3Di database to allow for easy testing.

Build the image:

    docker-compose build

Run the tests:

    docker-compose run modelchecker pytest

See `Creating revisions <threedi_modelchecker/migrations/README.rst>`_ for 
instructions on how to change the 3Di model schematisation.

Release
-------

Make sure you have zestreleaser_ installed.

    fullrelease

When you created a tag, make sure to upload it to pypi_.

.. _zestreleaser: https://zestreleaser.readthedocs.io/en/latest/
.. _pypi: https://pypi.org/project/threedi-modelchecker/
