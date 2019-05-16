from abc import ABC
from abc import abstractmethod

from geoalchemy2 import functions as geo_func
from geoalchemy2.types import Geometry
from sqlalchemy import func
from sqlalchemy import types

from ..threedi_model import constants
from ..threedi_model import models


class BaseCheck(ABC):
    def __init__(self, column):
        self.column = column
        self.table = column.table

    @abstractmethod
    def get_invalid(self, session):
        """Validate check on given session, return any rows which do not hold
        up to the condition this check is validating.

        :param session: sqlalchemy.orm.session.Session
        :return: list of named_tuples or empty list if there are no invalid
            rows
        """
        pass


class ForeignKeyCheck(BaseCheck):
    """Check all values in origin_column are in ref_column.

    Null values are ignored.

    """
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
    def get_invalid(self, session):
        duplicate_values = (
            session.query(self.column).group_by(self.column).having(
                func.count(self.column) > 1)
        )
        q = session.query(self.column.table).filter(
            self.column.in_(duplicate_values))
        return q.all()


class NullCheck(BaseCheck):
    def get_invalid(self, session):
        q = session.query(self.column.table).filter(self.column == None)
        return q.all()


class TypeCheck(BaseCheck):
    def get_invalid(self, session):
        if "sqlite" not in session.bind.dialect.dialect_description:
            return []

        expected_type = sqlalchemy_to_sqlite_type(self.column.type)
        q = session.query(self.column.table).filter(
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
    def get_invalid(self, session):
        invalid_geometries = session.query(self.column.table).filter(
            geo_func.ST_IsValid(self.column) != True,
            self.column != None
        )
        return invalid_geometries.all()


class GeometryTypeCheck(BaseCheck):
    def get_invalid(self, session):
        expected_geometry_type = _get_geometry_type(
            self.column,
            dialect=session.bind.dialect.name
        )
        invalid_geometry_types_q = session.query(self.column.table).filter(
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
    def get_invalid(self, session):
        invalid_values_q = session.query(self.column.table).filter(
            self.column.notin_(list(self.column.type.enum_class))
        )
        return invalid_values_q.all()


class BankLevelCheck(BaseCheck):
    def __init__(self):
        super().__init__(
            table=models.CrossSectionLocation,
            column=models.CrossSectionLocation.bank_level
        )

    def get_invalid(self, session):
        q = session.query(models.CrossSectionLocation).filter(
            models.CrossSectionLocation.bank_level == None,
            models.CrossSectionLocation.channel.has(
                models.Channel.calculation_type.in_(
                    [constants.CalculationType.CONNECTED,
                     constants.CalculationType.DOUBLE_CONNECTED]
                )
            ),
        )
        return q.all()
