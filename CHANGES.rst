Changelog of threedi-modelchecker
=================================


0.24.2 (2022-01-18)
-------------------

- Bugfix: DWF lateral upload wrong api call.

- Allow isolated manholes that are not connected to anything (emit warning instead
  of error).

- Added threedi_modelchecker.__version__.

- Added automatic release to PyPI.

- Use the threedi-api-client beta release instead of checking out from github.


0.24.1 (2022-01-17)
-------------------

- Bugfix: DWF lateral upload fails due to incorrect function arguments.


0.24 (2022-01-17)
-----------------

- Bugfix: Need to convert lateral geometry from str to dict representation.

- Add dem_obstacle_detection != True check.

- Added check on water_level_ini_type.

- Interpret empty strings the same as NULL in initial (groundwater) level file
  fields (simulation template worker).

- Set interpolate flag for boundary conditions from extractor default to True.

- Added dry weather flow calculation.


0.23 (2022-01-11)
-----------------

- Added security measures on connection for untrusted sqlite input.

- Added ThreediDatabase.check_integrity().

- Disabled temporary patch: require initial groundwaterlevel files to be present.


0.22 (2022-01-10)
-----------------

- Added legacy migrations down to version 160.


0.21 (2022-01-04)
-----------------

- Reduced level of bank level check to warning.

- Reduced level of v2_connection_nodes.the_geom_linestring to info.

- Minor typographic fixes.


0.20.2 (2021-12-28)
-------------------

- Convert v2_global settings enum values before using them in openapi models.

- Added checks for channel and culvert geometry distance to connection nodes.

- Added checks for illegal combinations of use_2d_flow, use_1d_flow, manhole_storage_area
  and dem file presence.

- Changed cross section location geometry check to WARNING.

- This release requires at least geoalchemy2 0.9.0.

- Changed some nullability and geometry validity checks to WARNING.

- Removed check 0101 (bank level not NULL check).

- Only warn on dist_calc_points <= 0 and MANNING friction_value >= 1.

- Make the cross_section_location.bank_level >= reference_level check a WARNING. It will
  be corrected anyway in make_tables.


0.20.1 (2021-12-17)
-------------------

- Temporary patch: do not error if initial groundwaterlevel file is not present.

- Bugfix: Structure controls upload in simulation template generation.


0.20 (2021-12-16)
-----------------

- Bugfix: Correct parsing of discharge_coefficients in table control.

- Removed timed control parsing, there are no models using it.

- Set maximum_time_step to sim_time_step if maximum_time_step is NULL or
  less than sim_time_step. Reverts change in 0.19.


0.19 (2021-12-15)
-----------------

- Set maximum_time_step to NULL where timestep_plus is not used.

- Replaced the generic timeseries check to more specific ones. The timeseries are
  not required anymore to be of the same length. Added checks are: timesteps should be
  >= 0 and increasing.


0.18 (2021-11-25)
-----------------

- Make cross section definition checks more informative.

- Display the table name instead of the internal model name in the error
  description.

- Accept schematisations with version 173 by re-implementing the last migration from
  the old stack.

- Updated settings checks to match the current API.


0.17 (2021-11-03)
-----------------

- Added `id` (boundary sqlite id)  and `type` (1D or 2D)  field to generated boundaries JSON file. 


0.16 (2021-11-02)
-----------------

- Added support for saving 1D initial waterlevel (from file), 2D initial waterlevel and initial groundwaterlevel in API. 
  Note: uses first initial waterlevel (aggregation) resource found for 1D, 2D or groundwater.

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
