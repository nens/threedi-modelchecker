# %% 
from typing import List, Union, Dict
from threedi_modelchecker.threedi_model.models import BoundaryConditions2D, BoundaryCondition1D
from threedi_modelchecker.threedi_database import ThreediDatabase
from sqlalchemy.orm import Query


from threedi_api_client.openapi.models.boundary_condition import BoundaryCondition

# %%

sqlite_file = "/srv/nens/models/t0224_velsen_velsen_noord/92e041d46a810d97fd6120ffa5ba0b81935f5d0d/velsen_noord_1d_reeks.sqlite"
database = ThreediDatabase(
    connection_settings={"db_path": sqlite_file}, db_type="spatialite"
)

session = database.get_session()

# [
#     {
#         "interpolate": false,
#         "values": [
#             [0, 0.5],
#             [500, 0,8],
#             [1000, 0]
#         ]
#     },
#     {
#         "interpolate": false,
#         "values": [
#             [0, 0,3],
#             [400, 0.1]
#         ]
#     },
#     {
#         "interpolate": false,
#         "values": [
#             [0, -2.4],
#             [1300, 0,3],
#             [3000, 1.2],
#             [3600, 0]
#         ]
#     }
# ]
# 2D boundaries need to be provided before 1D boundaries.

# 1D boundaries need to be in order of connectionnode id's.
# 2D boundaries need to be in order of id (of the boundary).

def boundary_2d_to_json_format(boundary_2d: BoundaryConditions2D) -> Dict:
    values = [[float(y) for y in x.split(",")] for x in boundary_2d.timeseries.split('\n')]

    # TODO: Do we need to take the boundary_type into account??
    return {
        "interpolate": False,
        "values": values
    }



def boundary_1d_to_json_format(boundary_1d: BoundaryCondition1D) -> Dict:
    values = [[float(y) for y in x.split(",")] for x in boundary_1d.timeseries.split('\n')]

    # TODO: Do we need to take the boundary_type into account??
    return {
        "interpolate": False,
        "values": values
    }


boundaries_2d = Query(BoundaryConditions2D).with_session(session).order_by(BoundaryConditions2D.id).all()
boundaries_1d = Query(BoundaryCondition1D).with_session(session).order_by(BoundaryCondition1D.connection_node_id).all()


all_boundaries = [boundary_2d_to_json_format(x) for x in boundaries_2d]
all_boundaries += [boundary_1d_to_json_format(x) for x in boundaries_1d]


print(all_boundaries)

# %%
