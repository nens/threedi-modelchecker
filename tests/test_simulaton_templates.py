import pytest
from sqlalchemy.sql.expression import extract, table
from threedi_api_client.openapi.models import ground_water_raster
from threedi_api_client.openapi.models.aggregation_settings import AggregationSettings
from threedi_api_client.openapi.models.ground_water_level import GroundWaterLevel
from threedi_api_client.openapi.models.lateral import Lateral
from threedi_api_client.openapi.models.numerical_settings import NumericalSettings
from threedi_api_client.openapi.models.one_d_water_level import OneDWaterLevel
from threedi_api_client.openapi.models.one_d_water_level_predefined import OneDWaterLevelPredefined
from threedi_api_client.openapi.models.physical_settings import PhysicalSettings
from threedi_api_client.openapi.models.time_step_settings import TimeStepSettings
from threedi_api_client.openapi.models.two_d_water_level import TwoDWaterLevel
from threedi_api_client.openapi.models.two_d_water_raster import TwoDWaterRaster
from tests import factories
from threedi_modelchecker.simulation_templates.exceptions import SchematisationError
from threedi_modelchecker.simulation_templates.boundaries.extractor import BoundariesExtractor
from threedi_modelchecker.simulation_templates.initial_waterlevels.extractor import InitialWaterlevelExtractor
from threedi_modelchecker.simulation_templates.laterals.extractor import LateralsExtractor
from threedi_modelchecker.simulation_templates.models import InitialWaterlevels, StructureControls
from threedi_modelchecker.simulation_templates.settings.extractor import SettingsExtractor
from threedi_modelchecker.simulation_templates.structure_controls.extractor import StructureControlExtractor
from threedi_modelchecker.threedi_model.constants import InitializationType
from threedi_modelchecker.simulation_templates.models import Settings
from threedi_modelchecker.threedi_model.models import Control, ControlGroup, ControlMeasureGroup, ControlMeasureMap, ControlMemory, ControlTable, ControlTimed


def test_boundary_conditions(session):
    for i in range(1, 3):
        factories.BoundaryConditions2DFactory.create(timeseries=f"0.0,-0.{i}\n0.1,-0.{i+1}")

    for i in range(3, 5):
        factories.BoundaryConditions1DFactory.create(timeseries=f"0.0,-0.{i}\n0.1,-0.{i+1}")

    
    extractor = BoundariesExtractor(session)
    values_check = [x['values'] for x in extractor.as_list()]
    assert values_check == [
        [[0.0, -0.1], [0.1, -0.2]],
        [[0.0, -0.2], [0.1, -0.3]],
        [[0.0, -0.3], [0.1, -0.4]],
        [[0.0, -0.4], [0.1, -0.5]]
    ] 
    
def test_boundary_conditions_incorrect_timeseries(session):
    factories.BoundaryConditions1DFactory.create(timeseries=f"0.0;-0.1")
    extractor = BoundariesExtractor(session)

    with pytest.raises(SchematisationError):
        extractor.as_list()


def test_initial_waterlevels(session):
    global_settings = factories.GlobalSettingsFactory.create(
        initial_waterlevel=-10, initial_waterlevel_file='test.tif',
        water_level_ini_type=InitializationType.MAX,
        initial_groundwater_level=-12)
    
    extractor = InitialWaterlevelExtractor(
        session, global_settings_id=global_settings.id)

    check = InitialWaterlevels(
        constant_2d=None,
        constant_1d=OneDWaterLevel(value=-10.0),
        constant_gw=GroundWaterLevel(value=-12.0),
        predefined_1d=None, 
        raster_2d=TwoDWaterRaster(aggregation_method="max", initial_waterlevel="test.tif"),
        raster_gw=None)

    assert extractor.all_initial_waterlevels() == check

    # Check constant 1d override by connection nodes
    factories.ConnectionNodeFactory.create(initial_waterlevel=10)

    extractor = InitialWaterlevelExtractor(
        session, global_settings_id=global_settings.id)

    check.constant_1d=None
    check.predefined_1d= OneDWaterLevelPredefined()

    assert extractor.all_initial_waterlevels() == check   

def test_laterals(session):
    factories.Lateral1dFactory.create()
    factories.Lateral2DFactory.create()

    extractor = LateralsExtractor(session)

    to_check = [
        Lateral(**{'offset': 0, 'interpolate': False, 'values': [[0.0, -0.2]], 'units': 'm3/s', 'point': {'type': 'point', 'coordinates': [-71.064544, 42.28787]}}),
        Lateral(**{'offset': 0, 'interpolate': False, 'values': [[0.0, -0.1]], 'units': 'm3/s', 'connection_node': 1})
    ]
    assert extractor.all_laterals() == to_check

def test_incorrect_lateral_1d_timeseries(session):
    factories.Lateral1dFactory.create(timeseries="0.0;0.2")
    with pytest.raises(SchematisationError):
        LateralsExtractor(session).all_laterals()

def test_incorrect_lateral_12_timeseries(session):
    factories.Lateral2DFactory.create(timeseries="0.0;0.2")    
    with pytest.raises(SchematisationError):
        LateralsExtractor(session).all_laterals()

 
def test_simulation_settings(session):
    num_settings = factories.NumericalSettingsFactory.create(id=1)
    global_settings = factories.GlobalSettingsFactory.create(id=1, numerical_settings_id=num_settings.id)
    factories.AggregationSettingsFactory.create(global_settings_id=global_settings.id)
    extractor = SettingsExtractor(session, global_settings_id=global_settings.id)

    to_check = Settings(
        numerical=NumericalSettings(**{
            'cfl_strictness_factor_1d': 1.0,
            'cfl_strictness_factor_2d': 1.0,
            'convergence_cg': 1e-09,
            'convergence_eps': 1e-09,
            'flooding_threshold': 0.01,
            'flow_direction_threshold': 1e-05,
            'friction_shallow_water_depth_correction': 0,
            'general_numerical_threshold': 1e-08,
            'limiter_slope_crossectional_area_2d': 0,
            'limiter_slope_friction_2d': 0,
            'limiter_slope_thin_water_layer': 0.01,
            'limiter_waterlevel_gradient_1d': 1,
            'limiter_waterlevel_gradient_2d': 1,
            'max_degree_gauss_seidel': 1,
            'max_non_linear_newton_iterations': 20,
            'min_friction_velocity': 0.01,
            'min_surface_area': 1e-08,
            'preissmann_slot': 0.0,
            'pump_implicit_ratio': 1.0,
            'time_integration_method': 0,
            'use_nested_newton': False,
            'use_of_cg': 0,
            'use_preconditioner_cg': 1}, 
        ),
        physical=PhysicalSettings(**{
            'use_advection_1d': 1,
            'use_advection_2d': 1}, 
        ),
        timestep=TimeStepSettings(**{
            'max_time_step': 1.0,
            'min_time_step': 0.1,
            'output_time_step': 1.0,
            'time_step': 30.0,
            'use_time_step_stretch': False}
        ),
        aggregations=[
            AggregationSettings(method='avg', flow_variable='water_level', interval=10.0)]
    )

    assert extractor.all_settings() == to_check


@pytest.fixture
def measure_group(session):
    measure_group: ControlMeasureGroup = factories.ControlMeasureGroupFactory.create(id=1)
    factories.ControlMeasureMapFactory.create(measure_group_id=measure_group.id)
    return measure_group


def test_structure_controls(session, measure_group):
    control_group: ControlGroup = factories.ControlGroupFactory.create(id=1, name="test group")
    table_control: ControlTable = factories.ControlTableFactory.create(id=1)
    memory_control: ControlMemory = factories.ControlMemoryFactory.create(id=1)
    timed_control: ControlTimed = factories.ControlTimedFactory.create(id=1)

    factories.ControlFactory.create(
        control_group_id=control_group.id, measure_group_id=measure_group.id,
        control_type="table", control_id=table_control.id)
    factories.ControlFactory.create(
        control_group_id=control_group.id, measure_group_id=measure_group.id,
        control_type="memory", control_id=memory_control.id)
    factories.ControlFactory.create(
        control_group_id=control_group.id, measure_group_id=None,
        control_type="timed", control_id=timed_control.id)

    extractor = StructureControlExtractor(session, control_group_id=control_group.id)
    
    to_check = StructureControls.from_dict({
        "memory": [
            {
                "offset": 0,
                "duration": 300,
                "measure_specification": {
                    "name": "test group",
                    "locations": [
                        {
                            "weight": "10",
                            "content_type": "v2_connection_node",
                            "content_pk": 101
                        }
                    ],
                    "variable": "s1",
                    "operator": ">"
                },
                "structure_id": 10,
                "structure_type": "v2_channel",
                "type": "set_discharge_coefficients",
                "value": [
                    0.0,
                    -1.0
                ],
                "upper_threshold": 1.0,
                "lower_threshold": -1.0,
                "is_active": True,
                "is_inverse": False
            }
        ],
        "table": [
            {
                "offset": 0,
                "duration": 300,
                "measure_specification": {
                    "name": "test group",
                    "locations": [
                        {
                            "weight": "10",
                            "content_type": "v2_connection_node",
                            "content_pk": 101
                        }
                    ],
                    "variable": "s1",
                    "operator": ">"
                },
                "structure_id": 10,
                "structure_type": "v2_channel",
                "type": "set_discharge_coefficients",
                "values": [
                    [
                        0.0,
                        -1.0
                    ]
                ]
            }
        ],
        "timed": [
            {
                "offset": 0,
                "duration": 300,
                "value": [
                    0.0,
                    -1.0
                ],
                "type": "set_discharge_coefficients",
                "structure_id": 10,
                "structure_type": "v2_channel"
            }
        ]   
    })

    assert extractor.all_controls().as_dict() == to_check.as_dict()

    
