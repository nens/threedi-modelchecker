threedi-modelchecker
====================

.. image:: https://img.shields.io/pypi/v/threedi-modelchecker.svg
        :target: https://pypi.org/project/threedi-modelchecker/

.. image:: https://github.com/nens/threedi-modelchecker/actions/workflows/test.yml/badge.svg
	:alt: Github Actions status
	:target: https://github.com/nens/threedi-modelchecker/actions/workflows/test.yml


A tool to verify the correctness of a 3Di schematisation.

It asserts the correctness of a 3Di schematisation and provides detailed 
information about any potential errors in it.

This package only work against a specific schematisation version. Use https://pypi.org/project/threedi-schema/ to upgrade
a schematisation version. See also the 3Di documentation at https://docs.3di.lizard.net/en/stable/d_before_you_begin.html#database-overview

Note that the name "modelchecker" might be slightly confusing: the thing that is checked is a schematisation, and not
a threedimodel. A schematisation is built interactively by the user and this schematisation will be converted to a
3Di-Model which can be used in simulations.

Installation
------------

    pip install threedi-modelchecker

Note that raster checks will be skipped unless GDAL is available.
``threedi-modelchecker`` is also integrated into the ThreediToolbox Qgis plugin: https://github.com/nens/ThreeDiToolbox

Example
-------

The following code sample shows how you can use the modelchecker to run all configured
checks and print an overview of all discovered errors::

    from threedi_modelchecker.exporters import format_check_results
    from threedi_modelchecker import ThreediModelChecker
    from threedi_schema import ThreediDatabase

    sqlite_file = "<Path to your sqlite file>"
    database = ThreediDatabase(sqlite_file)

    model_checker = ThreediModelChecker(database)
    for check, error in model_checker.errors(level="WARNING"):
        print(format_check_results(check, error))


Command-line interface
----------------------

Use the modelchecker from the command line as follows::

    threedi_modelchecker check -s path/to/model.sqlite -l warning 

By default, WARNING and INFO checks are ignored. To skip the beta features check,
add the --allow-beta flag.


Development
-----------

A docker image has been created for easy development. It contains an postgis 
server with an empty 3Di database to allow for easy testing.

Build the image:

    docker-compose build

Run the tests:

    docker-compose run modelchecker pytest

See `Creating revisions <https://github.com/nens/threedi-schema/blob/master/threedi_schema/migrations/README.rst>`_ for 
instructions on how to change the 3Di model schematisation.

Release
-------

Make sure you have zestreleaser_ installed.

    fullrelease

When you created a tag, make sure to upload it to pypi_.

.. _zestreleaser: https://zestreleaser.readthedocs.io/en/latest/
.. _pypi: https://pypi.org/project/threedi-modelchecker/
