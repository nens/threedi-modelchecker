from ..threedi_model import custom_types
from .base import EnumCheck
from .base import ForeignKeyCheck
from .base import GeometryCheck
from .base import GeometryTypeCheck
from .base import NotNullCheck
from .base import TypeCheck
from .base import UniqueCheck
from geoalchemy2.types import Geometry


def generate_foreign_key_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    foreign_key_checks = []
    for fk_column in table.foreign_keys:
        level = custom_level_map.get(fk_column.parent.name, "ERROR")
        foreign_key_checks.append(
            ForeignKeyCheck(
                reference_column=fk_column.column,
                column=fk_column.parent,
                level=level,
                **kwargs
            )
        )
    return foreign_key_checks


def generate_unique_checks(table, **kwargs):
    unique_checks = []
    for column in table.columns:
        if column.unique or column.primary_key:
            unique_checks.append(UniqueCheck(column, **kwargs))
    return unique_checks


def generate_not_null_checks(table, **kwargs):
    not_null_checks = []
    for column in table.columns:
        if not column.nullable:
            not_null_checks.append(NotNullCheck(column, **kwargs))
    return not_null_checks


def generate_type_checks(table, **kwargs):
    data_type_checks = []
    for column in table.columns:
        data_type_checks.append(TypeCheck(column, **kwargs))
    return data_type_checks


def generate_geometry_checks(table, **kwargs):
    geometry_checks = []
    for column in table.columns:
        if type(column.type) == Geometry:
            geometry_checks.append(GeometryCheck(column, **kwargs))
    return geometry_checks


def generate_geometry_type_checks(table, **kwargs):
    geometry_type_checks = []
    for column in table.columns:
        if type(column.type) == Geometry:
            geometry_type_checks.append(GeometryTypeCheck(column, **kwargs))
    return geometry_type_checks


def generate_enum_checks(table, custom_level_map=None, **kwargs):
    custom_level_map = custom_level_map or {}
    enum_checks = []
    for column in table.columns:
        if issubclass(type(column.type), custom_types.CustomEnum):
            level = custom_level_map.get(column.name, "ERROR")
            enum_checks.append(EnumCheck(column, level=level, **kwargs))
    return enum_checks
