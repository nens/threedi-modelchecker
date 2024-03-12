Changelog of threedi-modelchecker
=================================


2.7.0 (2024-03-12)
------------------
- Support geopackage
- Support changes in threedi-schema (0.220) needed for geopackage support


2.6.2 (2024-02-29)
------------------

- Add warning check (0616) for surfaces for which no inflow is generated because of the surface table not being referred to in global settings.
- Add warning check (0617) to warn if the surface table referred to in global settings is empty and no inflow will be generated for it.
- Remove warning check 0029.


2.6.1 (2024-02-20)
------------------

- Add warning check (1500) to warn about a friction value <= 1 for Chezy friction
- Add warning check (1501) to warn about friction values <= 1 or Chezy friction


2.6.0 (2024-01-31)
------------------

- Add error check (0020) for CrossSectionLocation.friction_value because that check is no longer included in the factory checks.
- Add error check (0080) for absent CrossSectionLocation.friction_value and CrossSectionDefinition.friction_values for TABULATED_YZ shape
- Add error check (0087) for correct formatting of space separated list of values for variable friction
- Add error check (0180) for variable friction and variable vegetation parameters only be used together with TABULATED_YZ shape
- Add error check (0181) for correct number of values for variable friction and variable vegetation parameters
- Add warning check (0182) for fixed and variable vegetation parameters in combination with non-conveyance friction
- Add warning check (0183) for fixed and variable vegetation parameters in combination with conveyance friction
- Add warning check (0184) for fixed and variable friction in combination with non-conveyance friction
- Add warning check (0185) for fixed and variable friction in combination with conveyance friction
- Add error check (0186) for using variable friction or vegetation with open, monotonically increasing z profile
- Add error check (0187) for correct formatting of space separated list of variable vegetation parameters
- Add error check (0188) for all friction values non-negative and smaller than 1 for Manning friction
- Add error check (0189) for all friction values non-negative for Chezy friction
- Add error check (0190) for non-negative fixed vegetation parameters
- Add error check (0191) for non-negative variable vegetation parameters
- Add error check (0192) for disallowing fixed vegetation with Manning friction
- Add error check (0193) for disallowing variable vegetation with Manning friction
- Add error check (0194) for requiring that either all or none fixed vegetation parameters are defined
- Add error check (0195) for requiring that either all or none variable vegetation parameters are defined



2.5.2 (2024-01-19)
------------------

- Order exported schematisation checks rst table to prevent unnecessarily large git diffs in threedi-docs.
  To facilitate this, sets of strings in error messages have been converted to lists of strings.


2.5.1 (2023-12-19)
------------------

- Use Type instead of type so the library works on Python 3.8.


2.5.0 (2023-12-18)
------------------

- Add warning check 208 to check if a(n) (impervious) surface's geometrical area
  differs by more than 1 m2 from its defined area

- Add info check 57 to check if pipes and culverts have closed cross-sections.

- Fix check 325; it was giving a warning whenever an interception_file was used.

- Add info check 802 for grid refinement levels equal to kmax.

- Add warning check 615 to check if a surface map references an invalid surface.

- Add error check 1405 to make sure that a DEM does not have more than 5e9 pixels.


2.4.0 (2023-09-19)
------------------

- Unmark checks 26, 27, 28 and 29 as beta.


2.3.0 (2023-08-14)
------------------

- Support marking checks as beta, so they will only be executed with allow_beta_features=True

- Add beta check 26 to make sure friction types with conveyance are only used on v2_cross_section_location

- Add beta check 27 to make sure friction types with conveyance are only used on tabulated rectangle,
  tabulated trapezium, or tabulated yz shapes.

- Add beta check 28 to make sure cross-sections with conveyance friction monotonically increase in width

- Add beta check 29 to advise users to use friction with conveyance on cross-sections where it is possible,
  but they haven't done so.

- Ignore TypeError raised on check 797 when grid_space is null.


2.2.4 (2023-06-15)
------------------

- Fixed check 204; it now only applies to broad crested weirs/orifices.


2.2.3 (2023-06-14)
------------------

- Ignore tiny floating-point deviations in RasterGridSizeCheck (check 798).

- Add check 327 to make sure vegetation drag is only used if the friction type is Chezy.

- Change log level of check 63 from ERROR to WARNING


2.2.2 (2023-05-17)
------------------

- Rewrite release workflow to use a supported github action for github release.

- Build the release with the build package instead of setuptools.


2.2.1 (2023-05-16)
------------------

- Fixed incorrect units in pumpstation check 66.


2.2.0 (2023-05-15)
------------------

- Added check 98: cross-section diameters must not be smaller than 0.1 m.

- Changed check 324 to 1151, to keep the aggregation settings checks grouped together.

- Clarified error message for check 206 and Use0DFlowCheck.

- Added --ignore-checks option on the modelchecker check command to ignore all checks matching a regex pattern.

- Added check 614 to make sure that no more than 50 surfaces are linked to a connection node.

- Added check 1152 to ensure all aggregation setting timesteps are the same.

- Added check 1153 to ensure all aggregation setting timesteps are less than the global settings timestep.

- Added check 1154 to ensure aggregation settings are present with all the aggregation_method-flow_variable pairs listed in the docs.

- Added checks 45 and 360 to ensure that channel, pipe and culvert dist_calc_points and global_settings dist_calc_points, respectively, are at least 5 metres.


2.1.1 (2023-05-08)
------------------

- Vegetation_drag column names have changed. Update column names in code.

- Bump threedi-schema version to 0.217.0.

- Raster checks 10001-10004 have been renamed to 1401-1404 to stay within 4 digits.

- Added check 1227: if v2_control.control_id references an id, the table it references must contain that id.

- Added check 56: the cross-sections on a channel must either all be open or all be closed.

- Added check 63: pumpstation capacity and storage at the end node must be set so the water level doesn't rise more than 1 m/s.

- Added check 613: the combined surface area linked to a connection node must not be more than 10000 m2.

- Added check 8: all of the ids in the database must be a positive signed 32-bit integer.


2.1.0 (2023-03-27)
------------------

- Add support for designating beta features in threedi-schema. If a user puts a
  non-null value in a column marked as beta in threedi-schema, a BetaFeaturesCheck
  error 1300 will be raised by the modelchecker. The allow-beta flag has been added
  to the CLI interface to disable this check temporarily.

- Add errors and warnings for vegetation_drag input. Both rasters and global values.

- Added check 73: groundwater boundaries are allowed only when there is
  groundwater hydraulic conductivity.

- Added check 74: groundwater boundary types are not allowed on 1D boundary
  conditions.

- Added groundwater 1D2D range checks for manholes, channels, and pipes for
  exchange_thickness, hydraulic_conductivity_in, and hydraulic_conductivity_out.


2.0.1 (2023-03-20)
------------------

- Pin minor version for threedi-schema dependency.


2.0.0 (2023-03-20)
------------------

- Add warning 108: the crest_level of a weir or orifice cannot be lower than
  the bottom_level of any manhole it is connected to.

- Add info 109 and 110: the bottom level of a manhole cannot be higher than
  the reference level of the closest cross-section of any channel it is
  connected to. threedigrid-builder automatically fixes this, hence info
  instead of warning.
- Rewrite command-line client. The ``--sqlite`` argument is now an argument of the
  ``check`` command, not of the main ``threedi_modelchecker`` group. To run a check,
  the new syntax is

  ``threedi_modelchecker check -s <your database>.sqlite -l <desired check level>``

- Add new command, ``export-checks``. This exports all checks executed by the model
  checker as an RsT table or in CSV format, as specified by the optional ``--format``
  argument. The check output can also be dumped to a file using ``--file``.

- Compatibility fix with rasterio 1.3.6.

- Drop SQLAlchemy 1.3 support, add 2.0 support.

- Add check 326: this gives an info message if a record exists in the simple_infiltration
  table, but is not referenced from the global settings.

- Add check 66: this raises a warning if a pumpstation empties its storage area in less than one timestep.

- Add check 1205 to make sure that a timeseries is not an empty string.

- Add checks 1206 to confirm that the timesteps in all boundary condition timesteps are the same.


1.0.1 (2023-02-02)
------------------

- Fixed warning 94; warn if height is not empty (instead of width).

- Fixed bug in check 81.


1.0.0 (2023-01-19)
------------------

- Separate the schema to a separate package: threedi-schema.

- Removed threedi_modelchecker.schema, threedi_database, threedi_model,
  ThreediDatabase. Import these from threedi-schema.

- Remove simulation templates generation code.


0.35.2 (2023-01-18)
-------------------

- Optimize check 275 (potential breach interdistance)

- Snap v2_calculation_point to their channel geometry (with a tolerance of 1E-7
  degrees) in migration 213 (v2_connected_pnt -> v2_potential_breach).

- Added range checks on exchange_line and potential_breach (265, 276, 277).

- Added check that a boundary condition timeseries starts at timestamp 0 (1204).

- Add checks for completely empty rasters (extended raster range checks 781-796).


0.35.1 (2023-01-11)
-------------------

- Fixed error messages 274 and 275.


0.35 (2023-01-10)
-----------------

- Schema version 214: remove v2_connected_pnt, v2_calculation_point,
  and v2_levee. The 'displaced' 1D2D points (mostly, breaches) are copied
  to v2_potential_breach, which also contains information about breaches.
  The levees are copied to v2_obstacle (which resets their primary key).
  Schema versions 211, 212 and 213 prepared for this change.

- Added error 274; a potential breach cannot be closer than 1m to the channel
  ending. It can be exactly on it (to allow breaches from connection nodes).

- Added error 275; a potential breach cannot be closer than 1m to another one.
  It can be exactly on another one (to allow 2 breach options on 1 node).

- Adapt warning 263: only emit a warning when an exchange line length is < 80%
  of the corresponding channel length.


0.34 (2022-12-12)
-----------------

- Added TABULATED_YZ (7) and INVERTED_EGG (8) cross section definition types.

- Added warning 94 for CIRCLE, EGG and INVERTED EGG crossections having a height.

- Added errors 95, 96 and 97 for invalid YZ profiles.


0.33 (2022-12-06)
-----------------

- Added v2_potential_breach and v2_exchange_line (schema version 211).

- Added RasterIO as an optional raster interface.

- The ThreediModelChecker context now accepts a "context_type" and "raster_interface"
  fields.

- Python 3.7 support is dropped.


0.32 (2022-11-16)
-----------------

- Added raster checks: file validity, has one band, has crs, range check.
  For DEM only it is also checked if pixels are square and crs is projected. 

- Added warning 325: interception_file given and interception_global not.

- Adapted errors 404, 405, 407, 410, 412, 414, 416, 419 to emit a warning when a
  raster is given but its corresponding global value is not. This global value
  will be used as a fallback value on pixels where the supplied raster has no data.

- Added error 421: v2_groundwater.groundwater_hydro_connectivity >= 0.

- New schema version (210): added v2_simple_infiltration.max_infiltration_capacity
  and corresponding checks 422 (>= 0) and 423 (warning when it is NULL and there is a file).

- Added error 424: v2_interflow.hydraulic_conductivity >= 0.

- Added error 425: v2_groundwater.initial_infiltration_rate >= 0.

- Added error 426: v2_groundwater.equilibrium_infiltration_rate >= 0.

- Added error 427: v2_groundwater.infiltration_decay_period > 0.

- Added warning 428 when v2_groundwater.groundwater_hydro_connectivity is NULL and
  a groundwater_hydro_connectivity_file is supplied.

- Migration to schema version 210 also fixes errors 421, 424, 425, 426, 427 by
  replacing negative values with NULL.

- All settings checks are now done only on the first global settings entry.

- Added "AllEqual" warnings (codes 330 and further) that check whether grid builder global
  settings are all the same in case there are multiple records.

- Added a unique check on v2_manhole.connection_node_id.


0.31 (2022-11-02)
-----------------

- Added error 324: warning when v2_aggregation_settings.flow_variable and
  .aggregation_method are not unique together.

- Added a check (207) for absence on index on connection_node geometry.

- Removed the side-effect of check 201 that enables spatial indexes.

- Added a check (254) for bottom_level presence for nodes without connected objects.

- Added ModelSchema.set_spatial_indexes and corresponding cli command.


0.30 (2022-10-24)
-----------------

- Emit an error for 0-width cross section definition. Before, only warnings were
  emitted.

- Changed flooding_threshold (numerical settings) maximum from 0.3 to 0.05.

- Removed PostGIS support.

- Removed v2_surface_map.surface_type.

- Check that refinement_level is not greater than kmax (E0800).

- Require at least python 3.7, sqlalchemy 1.3 and alembic 1.8 to fix a bug in migration 173.


0.28 (2022-09-20)
-----------------

- Updated schema to version 208: altered table settings (v2_global_settings):
  'maximum_table_step_size' was added and 'table_step_size_volume_2d'
  was removed.


0.27.1 (2022-05-31)
-------------------

- Fixed release script.


0.27.0 (2022-05-31)
-------------------

- Added ModelSchema().upgrade_spatialite_version (and the same argument to .upgrade) to
  upgrade the spatialite version from 3 to 4/5.

- Run unittests on spatialite 3 and 4.

- Improved performance of upgrading an empty database.

- Remove all NOT NULL, unique, and foreign key constraints in the spatialite.

- Fixed upgrade with backup=True on Windows.

- Added continuous integration on MacOS and Windows.


0.26.1 (2022-04-11)
-------------------

- The simulation template worker does not add default for maximum_time_step anymore.
  This wasn't necessary (the checker ensures that the setting is there when using
  time step stretch) and it lead to errors if the maximum_time_step was set to a value
  lower than sim_time_step when not using time step stretch.


0.26.0 (2022-03-17)
-------------------

- Automatically (re)create views in the spatialite after performing a schema upgrade.


0.25.4 (2022-03-10)
-------------------

- Fixed bug in timeseries checks 1201 and 1202.

- Prevent usage of GeoAlchemy 0.11 (because of a known issue).


0.25.3 (2022-02-07)
-------------------

- Add warning: cross section (tabulated) should start with 0.

- Pass temporary database copy file in a different context so it is opened
  one time, previously it was opened twice which results in errors on Windows.


0.25.2 (2022-01-26)
-------------------

- Re-enable Python 3.6 compatibility.


0.25.1 (2022-01-26)
-------------------

- Fix package.


0.25.0 (2022-01-26)
-------------------

- Updated DWF calculation to match ThreediToolBox update.

- Included Surface in DWF calculation. 


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
