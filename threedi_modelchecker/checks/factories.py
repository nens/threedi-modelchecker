from geoalchemy2.types import Geometry

from .base import ForeignKeyCheck
from .base import EnumCheck
from .base import GeometryCheck
from .base import GeometryTypeCheck
from .base import TypeCheck
from .base import NotNullCheck
from .base import UniqueCheck
from ..threedi_model import custom_types
from sqlalchemy.sql.schema import Table
from threedi_modelchecker.checks.base import ForeignKeyCheck
from typing import List
from threedi_modelchecker.checks.base import UniqueCheck
from threedi_modelchecker.checks.base import NotNullCheck
from threedi_modelchecker.checks.base import TypeCheck
from threedi_modelchecker.checks.base import GeometryCheck
from threedi_modelchecker.checks.base import GeometryTypeCheck
from threedi_modelchecker.checks.base import EnumCheck


def generate_foreign_key_checks(table: Table) -> List[ForeignKeyCheck]:
    foreign_key_checks = []
    for fk_column in table.foreign_keys:
        foreign_key_checks.append(
            ForeignKeyCheck(
                reference_column=fk_column.column,
                column=fk_column.parent)
        )
    return foreign_key_checks


def generate_unique_checks(table: Table) -> List[UniqueCheck]:
    unique_checks = []
    for column in table.columns:
        if column.unique or column.primary_key:
            unique_checks.append(UniqueCheck(column))
    return unique_checks


def generate_not_null_checks(table: Table) -> List[NotNullCheck]:
    not_null_checks = []
    for column in table.columns:
        if not column.nullable:
            not_null_checks.append(NotNullCheck(column))
    return not_null_checks


def generate_type_checks(table: Table) -> List[TypeCheck]:
    data_type_checks = []
    for column in table.columns:
        data_type_checks.append(TypeCheck(column))
    return data_type_checks


def generate_geometry_checks(table: Table) -> List[GeometryCheck]:
    geometry_checks = []
    for column in table.columns:
        if type(column.type) == Geometry:
            geometry_checks.append(GeometryCheck(column))
    return geometry_checks


def generate_geometry_type_checks(table: Table) -> List[GeometryTypeCheck]:
    geometry_type_checks = []
    for column in table.columns:
        if type(column.type) == Geometry:
            geometry_type_checks.append(GeometryTypeCheck(column))
    return geometry_type_checks


def generate_enum_checks(table: Table) -> List[EnumCheck]:
    enum_checks = []
    for column in table.columns:
        if issubclass(type(column.type), custom_types.CustomEnum):
            enum_checks.append(EnumCheck(column))
    return enum_checks
