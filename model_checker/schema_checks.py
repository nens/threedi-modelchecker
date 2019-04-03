from sqlalchemy import func, distinct, types
from geoalchemy2.types import Geometry

from model_checker import models
from model_checker.models import DECLARED_MODELS


def check_foreign_key(session, origin_column, ref_column):
    """Check all values in origin_column are in ref_column.

    Null values are ignored.

    :param session: sqlalchemy.orm.session.Session
    :param origin_column: InstrumentedAttribute
    :param ref_column: InstrumentedAttribute
    :return: list of declared models instances of origin_column.class
    """
    q = session.query(origin_column.table).filter(
        origin_column.notin_(session.query(ref_column)),
        origin_column != None
    )
    return q.all()


def check_unique(session, column):
    """Return all values in column that are not unique

    Null values are ignored.

    :param session: sqlalchemy.orm.session.Session
    :param column: InstrumentedAttribute
    :return: list of declared models instances of column.class
    """
    distinct_count = session.query(func.count(distinct(column))).scalar()
    all_count = session.query(func.count(column)).scalar()
    if distinct_count == all_count:
        return []
    duplicate_values = session.query(column).group_by(column).having(
        func.count(column) > 1)
    q = session.query(column.table).filter(column.in_(duplicate_values))
    return q.all()


def check_not_null(session, column):
    """Return all values that are not null

    :param self:
    :param session: sqlalchemy.orm.session.Session
    :param column: sqlalchemy.Column
    :return:
    """
    q = session.query(column.table).filter(column == None)
    return q.all()


def check_valid_type(session, column):
    """Return all values in column that are not of the column defined type.

    Null values are ignored.

    Only relevant for sqlite as it supports dynamic typing
    (https://www.sqlite.org/datatype3.html).

    :param session: sqlalchemy.orm.session.Session
    :param column: sqlalchemy.Column
    :return: list
    """
    if 'sqlite' not in session.bind.dialect.dialect_description:
        return []

    q = session.query(
        func.typeof(column)) \
        .group_by(func.typeof(column)) \
        .having(func.typeof(column) != 'null')
    type_count = q.count()
    if type_count == 0:
        return []
    expected_type = sqlalchemy_to_sqlite_type(column.type)
    if type_count == 1 and q.first()[0] == expected_type:
        return []
    q = session.query(column.table).filter(
        func.typeof(column) != expected_type,
        func.typeof(column) != 'null'
    )
    return q.all()


def sqlalchemy_to_sqlite_type(column_type):
    """Convert the sqlalchemy column type to sqlite data type

    :param column_type: sqlalchemy.column
    :return: (str)
    """
    if isinstance(column_type, types.String):
        return 'text'
    elif isinstance(column_type, types.Integer):
        return 'integer'
    elif isinstance(column_type, types.Float):
        return 'real'
    elif isinstance(column_type, types.Boolean):
        return 'integer'
    elif isinstance(column_type, types.Date):
        return 'text'
    elif isinstance(column_type, Geometry):
        return 'blob'
    else:
        raise TypeError("Unknown type: %s" % column_type)


def get_none_nullable_columns(table):
    """Return all non-nullable columns of the given table.

    :param table: sqlalchemy.sql.schema.Table
    :return: list of columns
    """
    not_null_columns = []
    for column in table.columns:
        if not column.nullable:
            not_null_columns.append(column)
    return not_null_columns


def get_foreign_key_columns(table):
    return table.foreign_keys


def check_valid_geom():
    pass


def check_timeseries_format():
    pass


# Constraints only added to the postgis (work) db in
# threedi-tools.sql.database_connections
# many more...
def has_two_connection_nodes(table_name):
    pass


def must_be_on_channel(windshielding_table_name):
    pass


class ThreediModelChecker:

    def __init__(self, threedi_db, declared_models=DECLARED_MODELS):
        self.db = threedi_db
        self.meta = threedi_db.get_metadata()
        self.declared_models = declared_models

    def check_not_null_columns(self):
        session = self.db.get_session()
        results = []
        columns_to_check = []
        for decl_model in self.declared_models:
            columns_to_check += get_none_nullable_columns(decl_model.__table__)
        for column in columns_to_check:
            results += check_not_null(session, column)
        return results

    def check_foreign_keys(self):
        session = self.db.get_session()
        result = []
        for decl_model in self.declared_models:
            foreign_keys = get_foreign_key_columns(decl_model.__table__)
            for fk in foreign_keys:
                result += check_foreign_key(session, fk.parent, fk.column)
        return result

    def check_data_types(self):
        session = self.db.get_session()
        result = []
        for decl_model in self.declared_models:
            for column in decl_model.__table__.columns:
                r = check_valid_type(session, column)
                if r:
                    print(column)
                result += r
        return result


class ModelCheckResult:

    status_code = None
    # Resolved/Unresolved

    severity = None
    # Error/Warning

    def __init__(self):
        pass
