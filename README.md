# Threedi-modelchecker

Threedi-modelchecker is a tool to verify the correctness of a 3Di model.
The goal is to provide a tool for model builders to quickly check if his/her 
model is correct and can run a 3Di simulation. It provides detailed 
information about any potential errors in the model.

Threedi-modelchecks works with both spatialite and postgis databases. However, 
the database should always have the latest 3Di migration: https://docs.3di.lizard.net/en/stable/d_before_you_begin.html#database-overview 

Installation:

    $ pip install threedi-modelchecker


Threedi-modelchecker is also integrated into the ThreediToolbox Qgis plugin: https://github.com/nens/ThreeDiToolbox

# Development

A docker image has been created for easy development. It contains an postgis 
server with an empty 3Di database to allow for easy testing.

Build the image:

    # docker-compose build

Run the tests:

    $ docker-compose run modelchecker pytest
