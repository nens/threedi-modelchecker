import os
from pprint import pprint
import sys

from pydantic import ValidationError

from threedi_modelchecker.threedi_model import models
from threedi_modelchecker.threedi_model import validators
from threedi_modelchecker.threedi_database import ThreediDatabase


MODELS = [
    models.AggregationSettings,
    models.BoundaryCondition1D,
    models.BoundaryConditions2D,
    models.CalculationPoint,
    models.Channel,
    models.ConnectedPoint,
    models.ConnectionNode,
    models.Control,
    models.ControlDelta,
    models.ControlGroup,
    models.ControlMeasureGroup,
    models.ControlMeasureMap,
    models.ControlMemory,
    models.ControlPID,
    models.ControlTable,
    models.ControlTimed,
    models.CrossSectionDefinition,
    models.CrossSectionLocation,
    models.Culvert,
    models.DemAverageArea,
    models.Floodfill,
    models.GlobalSetting,
    models.GridRefinement,
    models.GridRefinementArea,
    models.GroundWater,
    models.ImperviousSurface,
    models.ImperviousSurfaceMap,
    models.Interflow,
    models.Lateral1d,
    models.Lateral2D,
    models.Levee,
    models.Manhole,
    models.NumericalSettings,
    models.Obstacle,
    models.Orifice,
    models.Pipe,
    models.PumpedDrainageArea,
    models.Pumpstation,
    models.SimpleInfiltration,
    models.Surface,
    models.SurfaceMap,
    models.SurfaceParameter,
    models.Weir,
    models.Windshielding,
]

VALIDATORS = [
    validators.AggregationSettings,
    validators.BoundaryCondition1D,
    validators.BoundaryConditions2D,
    validators.CalculationPoint,
    validators.Channel,
    validators.ConnectedPoint,
    validators.ConnectionNode,
    validators.Control,
    validators.ControlDelta,
    validators.ControlGroup,
    validators.ControlMeasureGroup,
    validators.ControlMeasureMap,
    validators.ControlMemory,
    validators.ControlPID,
    validators.ControlTable,
    validators.ControlTimed,
    validators.CrossSectionDefinition,
    validators.CrossSectionLocation,
    validators.Culvert,
    validators.DemAverageArea,
    validators.Floodfill,
    validators.GlobalSetting,
    validators.GridRefinement,
    validators.GridRefinementArea,
    validators.GroundWater,
    validators.ImperviousSurface,
    validators.ImperviousSurfaceMap,
    validators.Interflow,
    validators.Lateral1d,
    validators.Lateral2D,
    validators.Levee,
    validators.Manhole,
    validators.NumericalSettings,
    validators.Obstacle,
    validators.Orifice,
    validators.Pipe,
    validators.PumpedDrainageArea,
    validators.Pumpstation,
    validators.SimpleInfiltration,
    validators.Surface,
    validators.SurfaceMap,
    validators.SurfaceParameter,
    validators.Weir,
    validators.Windshielding,
]


def main(database):
    database.check_connection()
    session = database.get_session()

    invalids = []
    for model, validator in zip(MODELS, VALIDATORS):
        print(f"--- VALIDATING {model}")
        to_validate = session.query(model)
        for instance in to_validate:
            try:
                validator.from_orm(instance)
            except ValidationError as e:
                print(e)
                # pprint(instance.__dict__)
                invalids.append(instance)

    print(invalids)
    print(len(invalids))
    print('finished')


if __name__ == '__main__':
    db_path = sys.argv[1]
    db_path = '/3di/models/v2_bergermeer/v2_bergermeer.sqlite'
    # db_path = '/3di/models/Frysland/wf_zw_052.sqlite'
    print('db_path: {}'.format(db_path))
    print(os.path.exists(db_path))

    sqlite_settings = {"db_path": db_path, "db_file": db_path}

    db = ThreediDatabase(sqlite_settings, db_type="spatialite")
    main(db)
