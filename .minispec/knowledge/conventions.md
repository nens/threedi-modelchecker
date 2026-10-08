# Conventions

Code and structural conventions for threedi-modelchecker development.

## Check Implementation Patterns
Checks are implemented by subclassing BaseCheck (threedi_modelchecker/checks/base.py)
or using QueryCheck to supply a SQLAlchemy Query that returns invalid rows.

Key points verified in source:
- BaseCheck implements: __init__(column, filters=None, level=CheckLevel.ERROR,
  error_code=0, is_beta_check=False), to_check(session), get_valid(session),
  description(), and column_name. Subclasses must implement get_invalid(session).
  (See threedi_modelchecker/checks/base.py)
- QueryCheck wraps a Query object (invalid) and applies optional filters before
  returning .all(). Use QueryCheck when the invalid set is expressible as a
  SQLAlchemy Query.
- There are many helper checks (ForeignKeyCheck, UniqueCheck, RangeCheck, etc.)
  in the same module implementing common patterns.

## Naming Conventions
Checks use an error_code integer and a level (CheckLevel enum). Error codes are
used for documentation and exporting; descriptions are provided by each check's
description() method. Check classes are named to reflect the constraint (e.g.
RasterExistsCheck, RasterIsValidCheck, UniqueCheck). Config-generated checks
live in threedi_modelchecker/config.py and follow numeric error_code groups.

## File Organization
Important paths (source of truth):

- Core API and orchestration
  - threedi_modelchecker/model_checks.py (ThreediModelChecker, EPSG inference)
  - threedi_modelchecker/config.py (Config and CHECKS registration/generation)
- Checks implementations
  - threedi_modelchecker/checks/base.py (BaseCheck, QueryCheck, helpers)
  - threedi_modelchecker/checks/*.py (individual domains and factories)
- Raster handling and contexts
  - threedi_modelchecker/checks/raster.py (LocalContext, ServerContext,
    BaseRasterCheck and raster checks)
  - threedi_modelchecker/interfaces/raster_interface.py (RasterInterface API)
- CLI & exporters
  - threedi_modelchecker/scripts.py (click CLI) and
    threedi_modelchecker/exporters.py
- Tests and fixtures
  - threedi_modelchecker/tests/ (conftest.py, data/empty.sqlite, empty.gpkg)

## Import Ordering

The project uses `isort` with Black-compatible profile. Run `isort .` before committing.

## Code Formatting

Black is used for code formatting with a line length of 88. Run `black threedi_modelchecker` before committing.

## Check Levels and Filtering

- Check levels are defined in threedi_modelchecker/checks/base.py as CheckLevel
  (ERROR=40, FUTURE_ERROR=39, WARNING=30, INFO=20). ThreediModelChecker.errors()
  accepts a level parameter and will iterate checks from Config filtered by the
  provided minimum level (see threedi_modelchecker/model_checks.py and
  threedi_modelchecker/config.py). The CLI exposes this via the `--level` flag
  (scripts.py).

## Session and Context usage

- The SQLAlchemy session used during checks is created from ThreediDatabase and
  the session receives a model_checker_context attribute set by
  ThreediModelChecker (threedi_modelchecker/model_checks.py). The context is an
  instance of LocalContext or ServerContext (threedi_modelchecker/checks/raster.py)
  and provides raster_interface, base_path (local) or available_rasters (server),
  and epsg_ref_code/epsg_ref_name used by EPSG-related checks.

## Exporters

- Exporters are in threedi_modelchecker/exporters.py. They provide:
  - print_errors / export_to_file (plain text output)
  - export_with_geom (returns structures including geometry when available)
  - generate_rst_table / generate_csv_table (used by scripts.export_checks)

## Testing fixtures and rollback

- Tests use fixtures in threedi_modelchecker/tests/conftest.py. A session fixture
  yields a SQLAlchemy session configured by ThreediDatabase.get_session(), has
  factories injected, sets s.model_checker_context = LocalContext(base_path=...)
  and yields the session. After the test the fixture calls s.rollback() to
  ensure no changes are persisted to the copied empty database files.

## Extension guidance

- To add checks, implement a BaseCheck subclass (get_invalid) or add a QueryCheck
  in threedi_modelchecker/config.py (preferred for simple SQL-expressible rules)
  or in checks/*.py and import/register in config.py. Use the error_code groups
  already present and provide a description() string. For raster checks, use
  LocalContext/ServerContext and the RasterInterface contract in
  threedi_modelchecker/interfaces/raster_interface.py.
