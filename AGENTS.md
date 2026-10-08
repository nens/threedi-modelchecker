# AGENTS.md

## Project Overview
**threedi-modelchecker**: validates 3Di schematisation databases (SQLite/SpatiaLite) using declarative checks. It's a CLI tool with both command-line and Python API interfaces.

## Python Environment
- Requires Python 3.10+
- Project manages multiple Python versions via pyenv (see `.envrc`)
- Use `pyenv local` to activate the correct environment before running commands
- CI tests Python 3.10–3.14 with pinned dependency versions per Python version (see `.github/workflows/test.yml`)

## Core Commands

### Testing
```bash
pytest                    # All tests
pytest path/to/test.py   # Specific test file
pytest -k test_name      # Specific test by name
pytest --cov             # Coverage report
```
**No special setup required**—tests use in-memory or temporary SpatiaLite databases. Test fixtures (`conftest.py`) handle database provisioning automatically. Never commit changes to `threedi_modelchecker/tests/data/{empty.sqlite, empty.gpkg}`—these are fixtures.

### Linting & Formatting
```bash
isort .                  # Sort imports (Black-compatible profile)
black threedi_modelchecker  # Format code
flake8 threedi_modelchecker # Lint (max line length: 88)
```
Pre-commit hooks (`.pre-commit-config.yaml`) run these automatically. Pre-commit excludes migrations, settings, and urls patterns.

### CLI Testing
```bash
threedi_modelchecker check -s path/to/model.sqlite -l ERROR
threedi_modelchecker export_checks --format rst
```
Entry point: `threedi_modelchecker.scripts:cli` (Click-based).

## Architecture

### Checks System
- **Base class**: `threedi_modelchecker.checks.base.BaseCheck`
- **Check levels**: ERROR (40), FUTURE_ERROR (39), WARNING (30), INFO (20)
- **Implementations**: `cross_section_definitions.py`, `location.py`, `other.py`, `raster.py`, `timeseries.py`
- **Registration**: `threedi_modelchecker.config.Config` instantiates checks from model definitions
- Checks are declarative; they operate on database queries via SQLAlchemy ORM

### Context Handling
- **LocalContext** (default): reads rasters from `data/rasters/` relative to the database
- **ServerContext**: for remote raster access (tests use LocalContext with `data_dir` fixture)
- Session attribute: `model_checker_context` carries raster/EPSG metadata

### Testing Data
- Fixtures in `conftest.py` create empty SpatiaLite v4 databases from template files
- Default EPSG: 28992 (Dutch RD)
- Factories inject test data via SQLAlchemy sessions; always rollback after tests (don't commit!)

## Important Constraints

### Import Order Matters
- Run checks in sequence: **lint (isort + black + flake8) → test**
- The linting workflow (`.github/workflows/lint.yml`) runs pre-commit; the test workflow (`.github/workflows/test.yml`) installs with test extras

### GDAL/Raster Dependencies
- Tests skip raster checks if GDAL is absent
- CI installs spatialite, libgdal-dev, and builds GDAL with `gdal-config`
- Raster checks require `rasterio` (optional dependency); test extras pull it in

### Version & Release
- Version managed in `threedi_modelchecker/__init__.py` (attribute `__version__`)
- Release via `fullrelease` (zest.releaser) to PyPI
- Changelog: `CHANGES.rst`

### Database Schema & Migrations
- Uses `threedi-schema` package (dependency); this package validates & upgrades schema, not modelchecker
- `alembic.ini` present but no local migrations directory—schema management is external
- modelchecker reads the schema via `ThreediDatabase.schema` and validates it

### No Local Monorepo
- Single package: `threedi_modelchecker/`
- Main entrypoints: `model_checks.ThreediModelChecker`, `scripts.cli`
- Config auto-discovered from `threedi_schema.domain.models.DECLARED_MODELS`

## Common Pitfalls
- **Don't commit test database snapshots**: `threedi_modelchecker/tests/data/{empty.sqlite, empty.gpkg}` are fixtures
- **SQLAlchemy version variance**: CI pins SQLAlchemy 1.4 (Python 3.10) vs 2.0 (Python 3.11+); test behavior may differ
- **EPSG code inference**: `get_epsg_data_from_raster()` tries rasters before geometry to find EPSG
- **Flake8 ignores**: E203, E266, E501, W503, E711, E712 (see `.flake8`)
