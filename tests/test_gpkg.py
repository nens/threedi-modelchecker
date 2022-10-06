from threedi_modelchecker.threedi_model import models


def test_read_geometry(gpkg_db):
    channel = gpkg_db.get_session().query(models.Channel).first()
    assert channel.code == "1"
    assert channel.the_geom is not None  # this is what happens with GeoAlchemy2
