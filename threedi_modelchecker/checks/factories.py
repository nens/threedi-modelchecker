from dataclasses import dataclass
from typing import Optional

from threedi_schema import custom_types

from .base import (
    EnumCheck,
    EPSGGeomCheck,
    ForeignKeyCheck,
    GeometryCheck,
    GeometryTypeCheck,
    NotNullCheck,
    TypeCheck,
    UniqueCheck,
)
from .raster import RasterHasMatchingEPSGCheck


@dataclass
class ForeignKeyCheckSetting:
    col: str
    ref: str
    filter: Optional[bool] = None


def get_level(table, column, level_map):
    level = level_map.get(f"*.{column.name}")
    level = level_map.get(f"{table.name}.{column.name}", level)
    return level or "ERROR"


def generate_foreign_key_checks(table, fk_settings, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    foreign_key_checks = []
    for fk_setting in fk_settings:
        if fk_setting.col.table != table:
            continue
        level = get_level(table, fk_setting.col, custom_level_map)
        # Prevent clash when kwargs contains 'filter'
        filter_val = (
            kwargs.get("filter") if fk_setting.filter is None else fk_setting.filter
        )
        kwargs.pop("filter", None)
        foreign_key_checks.append(
            ForeignKeyCheck(
                reference_column=fk_setting.ref,
                column=fk_setting.col,
                level=level,
                filters=filter_val,
                **kwargs,
            )
        )
    return foreign_key_checks


def generate_unique_checks(
    table, custom_level_map=None, extra_unique_columns=None, **kwargs
):
    custom_level_map = custom_level_map or {}
    unique_checks = []
    if extra_unique_columns is None:
        extra_unique_columns = []
    for column in table.columns:
        if (
            column.unique
            or column.primary_key
            or any(col.compare(column) for col in extra_unique_columns)
        ):
            level = get_level(table, column, custom_level_map)
            unique_checks.append(UniqueCheck(column, level=level, **kwargs))
    return unique_checks


def generate_not_null_checks(
    table, custom_level_map=None, extra_not_null_columns=None, **kwargs
):
    custom_level_map = custom_level_map or {}
    not_null_checks = []
    if extra_not_null_columns is None:
        extra_not_null_columns = []
    for column in table.columns:
        if not column.nullable or any(
            col.compare(column) for col in extra_not_null_columns
        ):
            level = get_level(table, column, custom_level_map)
            not_null_checks.append(NotNullCheck(column, level=level, **kwargs))
    return not_null_checks


def generate_type_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    data_type_checks = []
    for column in table.columns:
        level = get_level(table, column, custom_level_map)
        data_type_checks.append(TypeCheck(column, level=level, **kwargs))
    return data_type_checks


def generate_geometry_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    geometry_checks = []
    for column in table.columns:
        if isinstance(column.type, custom_types.Geometry):
            level = get_level(table, column, custom_level_map)
            geometry_checks.append(GeometryCheck(column, level=level, **kwargs))
    return geometry_checks


def generate_geometry_type_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    geometry_type_checks = []
    for column in table.columns:
        if isinstance(column.type, custom_types.Geometry):
            level = get_level(table, column, custom_level_map)
            geometry_type_checks.append(
                GeometryTypeCheck(column, level=level, **kwargs)
            )
    return geometry_type_checks


def generate_enum_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    enum_checks = []
    for column in table.columns:
        if issubclass(type(column.type), custom_types.CustomEnum):
            level = get_level(table, column, custom_level_map)
            enum_checks.append(EnumCheck(column, level=level, **kwargs))
    return enum_checks


def generate_epsg_geom_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    column = table.columns.get("geom")
    if column is not None:
        level = get_level(table, column, custom_level_map)
        return [EPSGGeomCheck(column=column, level=level, **kwargs)]
    else:
        return []


def generate_epsg_raster_checks(table, raster_columns, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    checks = []
    for column in table.columns:
        if column in raster_columns:
            level = get_level(table, column, custom_level_map)
            checks.append(
                RasterHasMatchingEPSGCheck(column=column, level=level, **kwargs)
            )
    return checks
