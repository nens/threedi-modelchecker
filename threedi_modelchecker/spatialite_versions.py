from sqlalchemy import inspect
from geoalchemy2 import func as geo_func
from geoalchemy2.types import Geometry
from .threedi_model import models
from sqlalchemy.exc import IntegrityError
from threedi_modelchecker.errors import UpgradeFailedError


def get_spatialite_version(db):
    with db.session_scope() as session:
        ((lib_version,),) = session.execute("SELECT spatialite_version()").fetchall()

    # Identify Spatialite version
    inspector = inspect(db.get_engine())
    spatial_ref_sys_cols = [x["name"] for x in inspector.get_columns("spatial_ref_sys")]
    if len(spatial_ref_sys_cols) == 0:
        raise ValueError("Not a spatialite file")

    if "srs_wkt" in spatial_ref_sys_cols:
        file_version = 3
    else:
        file_version = 4

    return int(lib_version.split(".")[0]), file_version


def cast_if_geometry(column):
    """Cast Geometry columns to EWKT (so that we can save it right back later)"""
    if isinstance(column.type, Geometry):
        return geo_func.AsEWKT(column).label(column.name)
    else:
        return column


def model_query(session, model):
    """Query fields explicitly, so that we end up with an iterator of row tuples"""
    return session.query(*[cast_if_geometry(c) for c in model.__table__.columns])


def model_from_tuple(model, tpl):
    return model(**{c.key: v for (c, v) in zip(model.__table__.columns, tpl)})


def copy_model(from_db, to_db, model):
    with from_db.session_scope() as input_session:
        objs = [model_from_tuple(model, x) for x in model_query(input_session, model)]
        if len(objs) == 0:
            return
    with to_db.session_scope() as work_session:
        try:
            work_session.bulk_save_objects(objs)
        except IntegrityError as e:
            work_session.rollback()
            raise UpgradeFailedError(e.orig.args[0])
        else:
            work_session.commit()


def copy_models(from_db, to_db, models=models.DECLARED_MODELS):
    for model in models:
        copy_model(from_db, to_db, model)
