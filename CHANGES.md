Changelog of threedi-modelchecker
===================================================


0.2 (unreleased)
----------------

- Renamed some methods of ThreediModelChecker.
- Added basic to the 3di model schema: checks if the model has the latest migration 
  applied and raises an error if not.


0.1 (2019-06-04)
----------------

- Initial project structure.
- Added ORM for a threedi-model in sqlalchemy.
- Added several types of checks.
- Manually configured many checks.
- Added check factories, which generate many checks based on the ORM.
