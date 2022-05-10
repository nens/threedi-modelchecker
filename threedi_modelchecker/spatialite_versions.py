from sqlalchemy import inspect
from .threedi_model import models

def get_spatialite_version(db):
    with db.session_scope() as session:
        (lib_version, ), = session.execute("SELECT spatialite_version()").fetchall()
    
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


def copy_obj(obj):
    d = dict(obj.__dict__)
    d.pop("_sa_instance_state") # get rid of SQLAlchemy special attr
    return obj.__class__(**d)


def copy_model(from_db, to_db, model):
    with from_db.session_scope() as input_session:
        objs = [copy_obj(x) for x in input_session.query(model).all()]
        if len(objs) == 0:
            return
    with to_db.session_scope() as work_session:
        work_session.bulk_save_objects(objs)
        work_session.commit()


def copy_models(from_db, to_db, models=models.DECLARED_MODELS):
    for model in models:
        copy_model(from_db, to_db,model)
