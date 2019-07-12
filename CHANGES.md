Changelog of threedi-modelchecker
===================================================


0.5 (2019-07-12)
----------------

- Retry release (release of 0.4 is missing changes).


0.4 (2019-07-12)
----------------

- Update to readme.
- No longer raise a MigrationTooHighError when the migration is larger than expected.


0.3 (2019-07-08)
----------------

- Fixed TypeError with CrossSectionShapeCheck when width/height are `None`.
- Updated some constraints on CrossSectionShapeCheck:
  - Heights of tabulated shape must be increasing.
  - Egg only requires a width, which must be greater than 0.
- Added 0 to a valid value for ZoomCategories. Also renamed the ZoomCategories names 
  to something clear names.


0.2 (2019-06-12)
----------------

- Renamed some methods of ThreediModelChecker.
- Added basic to the 3di model schema: checks if the model has the latest migration 
  applied and raises an error if not.
- Rewrote CrossSectionShape check to no longer use regex and added it to config.


0.1 (2019-06-04)
----------------

- Initial project structure.
- Added ORM for a threedi-model in sqlalchemy.
- Added several types of checks.
- Manually configured many checks.
- Added check factories, which generate many checks based on the ORM.
