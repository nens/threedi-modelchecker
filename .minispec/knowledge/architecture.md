# Architecture

This document describes the overall structure and design of threedi-modelchecker.

## Overview

threedi-modelchecker is a Python CLI and library that validates 3Di schematisation
databases (SQLite / SpatiaLite / GeoPackage) using a large set of declarative
checks. It is implemented for Python 3.10+ and relies on threedi_schema for the
database schema, SQLAlchemy (+ geoalchemy2) for queries, and optional GDAL/raster
support via a RasterInterface. See pyproject.toml for dependency constraints.

## Key Components

- Checks system (threedi_modelchecker/checks/ and checks/factories)
  - Base contract and implementations live in threedi_modelchecker/checks/base.py
    (BaseCheck, QueryCheck and many concrete checks). See
    threedi_modelchecker/checks/base.py for the CheckLevel enum and check
    behaviour.
  - Large collection of concrete checks and factories are defined under
    threedi_modelchecker/checks/ (e.g. cross_section_definitions.py,
    raster.py, location.py, other.py, timeseries.py) and are assembled in
    threedi_modelchecker/config.py (Config and CHECKS generation).

- Context handling and raster support
  - LocalContext and ServerContext dataclasses live in
    threedi_modelchecker/checks/raster.py and are used to resolve raster
    paths and raster interfaces (default GDALRasterInterface). Raster
    interface contract is defined in
    threedi_modelchecker/interfaces/raster_interface.py.

- CLI and API
  - CLI entrypoints are in threedi_modelchecker/scripts.py (Click commands
    `check` and `export_checks`). The high-level API class is
    ThreediModelChecker in threedi_modelchecker/model_checks.py which wires the
    schema, Config and Context together and exposes .checks() and .errors().

- Exporters
  - Result formatting and exporters are in
    threedi_modelchecker/exporters.py (print_errors, export_to_file,
    export_with_geom, generate_rst_table, generate_csv_table).

- Tests and fixtures
  - Test fixtures live in threedi_modelchecker/tests/conftest.py. Tests create
    temporary copies of empty.sqlite / empty.gpkg from
    threedi_modelchecker/tests/data/ and use a session fixture that rolls back
    after every test.

## Dependencies

See `pyproject.toml` for the current dependency list and version constraints.
