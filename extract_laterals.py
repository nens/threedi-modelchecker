# %% 
from typing import List, Union
from threedi_modelchecker.threedi_model.models import Lateral1d, Lateral2D
from threedi_modelchecker.threedi_database import ThreediDatabase
from sqlalchemy.orm import Query
from geoalchemy2 import func
from geoalchemy2.shape import to_shape 
from threedi_api_client.openapi.models.lateral import Lateral


# %%
sqlite_file = "/srv/nens/models/u0238_papendrecht/2602caf5138245e3d4f59f547e5911547a3cb54f/papendrecht_integraal.sqlite"

sqlite_file = "/srv/nens/models/testbank_3di/206_2D_interflw_lateral/206_2D_interflw_lateral.sqlite"
sqlite_file = "/srv/nens/models/testbank_3di/137_2D_FlowObstacleWall_lateral/137_2D_FlowObstacleWall_lateral.sqlite"

database = ThreediDatabase(
    connection_settings={"db_path": sqlite_file}, db_type="spatialite"
)

session = database.get_session()

laterals_1d = Query(Lateral1d).with_session(session).all()
laterals_2d = Query(Lateral2D).with_session(session).all()


def lateral_1d_to_api_lateral(lateral_1d: Lateral1d) -> Lateral:
    values = [[float(y) for y in x.split(",")] for x in lateral_1d.timeseries.split('\n')]

    offset = values[0][0]

    if offset > 0:
        # Shift timeseries to start at t=0 
        values = [[x[0] - offset, x[1]] for x in values]

    return Lateral(
        connection_node=int(lateral_1d.connection_node_id),
        offset=int(values[0][0]),
        duration=int(values[-1][0]),
        values=values,
        units="m3/s",
        interpolate=False
    )


def lateral_2d_to_api_lateral(lateral_2d: Lateral2D) -> Lateral:
    values = [[float(y) for y in x.split(",")] for x in lateral_2d.timeseries.split(' ')]

    offset = values[0][0]

    if offset > 0:
        # Shift timeseries to start at t=0 
        values = [[x[0] - offset, x[1]] for x in values]

    # x,y is correct (4.294348493375471, 52.033176579129936) until we alter the API
    shp = to_shape(lateral_2d.the_geom)
    point = {
        "type": "point",
        "coordinates": [shp.x, shp.y]
    }

    return Lateral(
        offset=int(values[0][0]),
        duration=int(values[-1][0]),
        values=values,
        point=point,
        units="m3/s",
        interpolate=False
    )

   
for x in laterals_1d:
    print(lateral_1d_to_api_lateral(x))


for x in laterals_2d:
    print(lateral_2d_to_api_lateral(x))


# %%
