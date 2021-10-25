Changelog of threedi-modelchecker
=================================


0.15 (2021-10-25)
-----------------

- Simulation templates can be saved (asynchroniously) to the API

- Added support for extracting simulation template information from
  an sqlite file. This information includes: settings, boundary conditions,
  laterals, structure controls and initial waterlevels.

- Added log levels (INFO, WARNING, ERROR). The level of the checker can be
  adjusted through ThreediModelChecker().errors and .checks. The command-line
  interface also supports the --level parameter.

- Fixed formatting of the command-line interface output.

- Removed the summarize (--sum, --no-sum) option from the command-line interface.

- Complete run through of the checks.

- Added an error codes to each check.

- Added an initial migration (0200) that adds the tables only when necessary. In
  this way, empty and existing sqlite files can be initialized.

- Added a migration (0201) that replaces friction_type=4 with 2.

- Added a migration (0202) that removes all v1 tables and views.

- Added a migration (0203) that drops v2_connection_nodes.the_geom_linestring and
  v2_aggregation_settings.aggregation_in_space.

- Fixed compatibility with SQLAlchemy 1.4.*.


0.14 (2021-07-29)
-----------------

- Added FileExistsCheck.


0.13 (2021-06-17)
-----------------

- Fixed Pumpstation.lower_stop_level check.


0.12 (2021-04-19)
-----------------

- Added ThreediDatabase.session_scope context manager.

- Set WARNING in description of check on storage area of an isolated manhole.

- Added database schema revision management using alembic. The ModelSchema has
  two new methods: .get_version() and .upgrade(). 


0.11 (2021-01-26)
-----------------

- Add check `ConnectionNodesDistance` which ensure all connection_nodes have a minimum
  distance between each other.
- Set the geometry of the following tables as required: impervious_surface, obstacle,
  cross_section_location, connection_nodes, grid_refinement, surface,
  2d_boundary_conditions and 2d_lateral.
- Add check for open cross-section when NumericalSettings.use_of_nested_newton is
  turned off.
- Add checks to ensure some of the fields in numericalSettings are larger than 0.
- Add check to ensure an isolated pipe always has a storage area.
- Add check to see if a connection_node is connected to an artifact
  (pipe/channel/culvert/weir/pumpstation/orifice).


0.10.2 (2020-09-15)
-------------------

- Changed Pipe.calculation_type to include broad- and shortcrest.

- Bugfix: Pumpstation.lower_stop_level should be higher than
  models.Manhole.bottom_level.


0.10.1 (2020-05-18)
-------------------

- Bugfix: made the `ConnectionNodesLength` backwards compatible with sqlalchemy 1.1.


0.10 (2020-05-06)
-----------------

- Added `ConnectionNodesLength` check to check the length between a start- and end node
  is above a certain threshold. Configured this check for pipes, weirs and orifices.

- Configured checks to see if the length of a linestring geometry is larger than 0.05m
  for culverts and channels.

- Chaned GlobalSettings.start_date and GlobalSetting.start_time into type Text and
  added two checks to see if the fields are valid datetime and date respectively.

- Configured extra check: use_1d_flow must be set to True when your model has 1d
  elements.

- Removed `ConditionalCheck` and replaced it with `QueryCheck`.

- Added type-hinting.

- Created `CustomEnum` for `Enum` objects.


0.9 (2019-11-27)
----------------

- Fixed some misconfigured checks, see https://github.com/nens/threedi-modelchecker/issues/10.


0.8 (2019-11-26)
----------------

- Set language of travis to python and test for python 3.6 and 3.7.

- Update to following columns to be non-nullable: Levee.the_geom,
  Culvert.invert_level_start_point and Culvert.invert_level_end_point.

- Removed threedigrid from requirements.

- Configured extra checks: Pumpstation.lower_stop_level > Manhole.bottom_level.

- Configured extra checks: Pipe.invert_level >= .Manhole.bottom_level.

- Added additional check type: QueryCheck.


0.7 (2019-07-18)
----------------

- Fix setup.py.


0.6 (2019-07-18)
----------------

- Added missing NotNullChecks to the config.py


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
