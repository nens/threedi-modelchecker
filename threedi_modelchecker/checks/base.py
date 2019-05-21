from abc import ABC
from abc import abstractmethod

from geoalchemy2 import functions as geo_func
from geoalchemy2.types import Geometry
from sqlalchemy import func
from sqlalchemy import types


class BaseCheck(ABC):
    """Baseclass for all checks.

    A Check defines a constraint on a specific column and its table.
    One can validate if the constrain holds using the method `get_invalid()`.
    This method will return a list of rows (as named_tuples) which are invalid.
    """
    def __init__(self, column):
        self.column = column
        self.table = column.table

    @abstractmethod
    def get_invalid(self, session):
        """Return a list of rows (named_tuples) which are invalid.

        What is invalid is defined in the check. Returns an empty list if no
        invalid rows are present.

        :param session: sqlalchemy.orm.session.Session
        :return: list of named_tuples or empty list if there are no invalid
            rows
        """
        pass

    def __repr__(self):
        return "<%s: %s.%s>" % (
            type(self).__name__,
            self.table.name,
            self.column.name
        )


class ForeignKeyCheck(BaseCheck):
    """Check all values in `column` are in `reference_column`.

    Null values are ignored."""
    def __init__(self, reference_column, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reference_column = reference_column

    def get_invalid(self, session):
        q = session.query(self.table).filter(
            self.column.notin_(session.query(self.reference_column)),
            self.column != None
        )
        return q.all()


class UniqueCheck(BaseCheck):
    """Check all values in `column` are unique

    Null values are ignored."""
    def get_invalid(self, session):
        duplicate_values = (
            session.query(self.column).group_by(self.column).having(
                func.count(self.column) > 1)
        )
        q = session.query(self.column.table).filter(
            self.column.in_(duplicate_values))
        return q.all()


class NotNullCheck(BaseCheck):
    """"Check all values in `column` that are not null"""
    def get_invalid(self, session):
        q = session.query(self.table).filter(self.column == None)
        return q.all()


class TypeCheck(BaseCheck):
    """Check all values in `column` that are of the column defined type.

    Null values are ignored."""
    def get_invalid(self, session):
        if "sqlite" not in session.bind.dialect.dialect_description:
            return []

        expected_type = sqlalchemy_to_sqlite_type(self.column.type)
        q = session.query(self.table).filter(
            func.typeof(self.column) != expected_type,
            func.typeof(self.column) != "null"
        )
        return q.all()


def sqlalchemy_to_sqlite_type(column_type):
    """Convert the sqlalchemy column type to sqlite data type

    Returns the value similar as the sqlite 'typeof' function.
    Raises TypeError if the column type is unknown.

    :param column_type: sqlalchemy.column
    :return: (str)
    """
    if isinstance(column_type, types.TypeDecorator):
        column_type = column_type.impl

    if isinstance(column_type, types.String):
        return "text"
    elif isinstance(column_type, types.Float):
        return "real"
    elif isinstance(column_type, types.Integer):
        return "integer"
    elif isinstance(column_type, types.Boolean):
        return "integer"
    elif isinstance(column_type, types.Numeric):
        return "numeric"
    elif isinstance(column_type, types.Date):
        return "text"
    elif isinstance(column_type, Geometry):
        return "blob"
    elif isinstance(column_type, types.TIMESTAMP):
        return "text"
    else:
        raise TypeError("Unknown column type: %s" % column_type)


class GeometryCheck(BaseCheck):
    """Check all values in `column` are a valid geometry.

    Null values are ignored."""
    def get_invalid(self, session):
        invalid_geometries = session.query(self.table).filter(
            geo_func.ST_IsValid(self.column) != True,
            self.column != None
        )
        return invalid_geometries.all()


class GeometryTypeCheck(BaseCheck):
    """Check all values in `column` are of geometry type in defined in
    `column`.

    Null values are ignored"""
    def get_invalid(self, session):
        expected_geometry_type = _get_geometry_type(
            self.column,
            dialect=session.bind.dialect.name
        )
        invalid_geometry_types_q = session.query(self.table).filter(
            geo_func.ST_GeometryType(self.column) != expected_geometry_type,
            self.column != None
        )
        return invalid_geometry_types_q.all()


def _get_geometry_type(column, dialect):
    if dialect == 'sqlite':
        return column.type.geometry_type
    elif dialect == 'postgresql':
        geom_type = column.type.geometry_type.capitalize()
        return 'ST_%s' % geom_type
    else:
        raise TypeError("Unexpected dialect %s" % dialect)


class EnumCheck(BaseCheck):
    """Check all values in `column` are within the defined Enum values of
    `column`.

    Unexpected values are values not defined by its enum_class.

    Null values are ignored"""
    def get_invalid(self, session):
        invalid_values_q = session.query(self.table).filter(
            self.column.notin_(list(self.column.type.enum_class))
        )
        return invalid_values_q.all()


class RangeCheck(BaseCheck):
    """Check all values in `column` are within specified bounds

    Null values are ignored."""
    def __init__(self, lower_limit=None, upper_limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def get_invalid(self, session):
        q = session.query(self.table)
        if self.lower_limit is not None and self.upper_limit is not None:
            q = q.filter(
                (self.column < self.lower_limit)
                | (self.column > self.upper_limit)
            )
        elif self.lower_limit is not None:
            q = q.filter(self.column < self.lower_limit)
        elif self.upper_limit is not None:
            q = q.filter(self.column > self.upper_limit)
        return q.all()
