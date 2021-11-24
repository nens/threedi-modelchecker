import pytest
from pathlib import Path
from unittest import mock
from threedi_api_client.openapi.models import Simulation
from threedi_api_client.openapi.models.aggregation_settings import AggregationSettings
from threedi_api_client.openapi.models.file_structure_control import (
    FileStructureControl,
)
from threedi_api_client.openapi.models.initial_waterlevel import InitialWaterlevel
from threedi_api_client.openapi.models.ground_water_level import GroundWaterLevel
from threedi_api_client.openapi.models.raster import Raster
from threedi_api_client.openapi.models.lateral import Lateral
from threedi_api_client.openapi.models import FileLateral, FileBoundaryCondition
from threedi_api_client.openapi.models.numerical_settings import NumericalSettings
from threedi_api_client.openapi.models.one_d_water_level import OneDWaterLevel
from threedi_api_client.openapi.models.one_d_water_level_file import OneDWaterLevelFile
from threedi_api_client.openapi.models.physical_settings import PhysicalSettings
from threedi_api_client.openapi.models.time_step_settings import TimeStepSettings
from threedi_api_client.openapi.models.two_d_water_raster import TwoDWaterRaster
from tests import factories
from threedi_modelchecker.simulation_templates.exceptions import SchematisationError
from threedi_modelchecker.simulation_templates.boundaries.extractor import (
    BoundariesExtractor,
)
from threedi_modelchecker.simulation_templates.extractor import (
    SimulationTemplateExtractor,
)
from threedi_modelchecker.simulation_templates.initial_waterlevels.extractor import (
    InitialWaterlevelExtractor,
)
from threedi_modelchecker.simulation_templates.laterals.extractor import (
    LateralsExtractor,
)
from threedi_modelchecker.simulation_templates.models import (
    InitialWaterlevels,
    StructureControls,
    TemplateValidationError,
)
from threedi_modelchecker.simulation_templates.settings.extractor import (
    SettingsExtractor,
)
from threedi_modelchecker.simulation_templates.structure_controls.extractor import (
    StructureControlExtractor,
)
from threedi_api_client.openapi.models import UploadEventFile
from threedi_modelchecker.threedi_model.constants import InitializationType
from threedi_modelchecker.simulation_templates.models import (
    Settings,
    SimulationTemplate,
    get_upload_instance,
)
from threedi_modelchecker.threedi_model.models import (
    ControlGroup,
    ControlMeasureGroup,
    ControlMemory,
    ControlTable,
    ControlTimed,
)


try:
    from unittest.mock import AsyncMock, Mock
except ImportError:
    # Python 3.7
    from mock.mock import AsyncMock, Mock


@pytest.fixture
async def upload_file_m():
    with mock.patch(
        "threedi_modelchecker.simulation_templates.models.upload_fileobj",
        new_callable=AsyncMock,
    ) as upload_file:
        yield upload_file


@pytest.fixture
async def simulation() -> Simulation:
    simulation = Simulation(
        id=1,
        name="sim-1",
        threedimodel=1,
        organisation="b08433fa47c1401eb9cbd4156034c679",
        start_datetime="2021-10-06T09:32:38.222",
        duration=3600,
    )
    return simulation


@pytest.fixture
async def client():
    api = AsyncMock()

    async def mocked_get_upload_instance(api_func, simulation_pk: int, filename: str):
        # Mock lookup function for getting lateral-file and boundary condition file resources
        if "laterals" in filename:
            return FileLateral(
                id=10, simulation=1, offset=10, file=None, state="processing"
            )
        elif "boundaries" in filename:
            return FileBoundaryCondition(
                id=11, simulation=1, file=None, state="processing"
            )
        elif "controls" in filename:
            return FileStructureControl(
                id=12, simulation=1, offset=9, file=None, state="processing"
            )
        return None

    with mock.patch(
        "threedi_modelchecker.simulation_templates.models.get_upload_instance",
        wraps=mocked_get_upload_instance,
    ):
        yield api.return_value


@pytest.fixture
def measure_group(session):
    measure_group: ControlMeasureGroup = factories.ControlMeasureGroupFactory.create(
        id=1
    )
    factories.ControlMeasureMapFactory.create(measure_group_id=measure_group.id)
    return measure_group


@pytest.fixture
def simulation_template(session, measure_group):
    factories.Lateral1dFactory.create()
    factories.Lateral2DFactory.create()

    factories.BoundaryConditions2DFactory.create(timeseries="0,-0.1\n1,-0.2")

    factories.BoundaryConditions1DFactory.create(timeseries="0,-0.3\n1,-0.4")

    control_group: ControlGroup = factories.ControlGroupFactory.create(
        id=1, name="test group"
    )
    table_control: ControlTable = factories.ControlTableFactory.create(id=1)
    memory_control: ControlMemory = factories.ControlMemoryFactory.create(id=1)
    timed_control: ControlTimed = factories.ControlTimedFactory.create(id=1)

    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=measure_group.id,
        control_type="table",
        control_id=table_control.id,
    )
    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=measure_group.id,
        control_type="memory",
        control_id=memory_control.id,
    )
    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=None,
        control_type="timed",
        control_id=timed_control.id,
    )

    num_settings = factories.NumericalSettingsFactory.create(id=1)
    global_settings = factories.GlobalSettingsFactory.create(
        id=1,
        numerical_settings_id=num_settings.id,
        initial_waterlevel=-9999,
        initial_waterlevel_file="test.tif",
        water_level_ini_type=InitializationType.MAX,
        initial_groundwater_level_file="test2.tif",
        initial_groundwater_level_type=InitializationType.MIN,
        control_group_id=control_group.id,
    )

    # Check constant 1D initial waterlevel from file
    factories.ConnectionNodeFactory.create(initial_waterlevel=10)

    factories.AggregationSettingsFactory.create(global_settings_id=global_settings.id)

    extractor = SimulationTemplateExtractor(Path("/tmp/nothing.sqlite"))

    global_settings_options = extractor._get_global_settings_options(session)
    assert len(global_settings_options) == 1

    simulation_template: SimulationTemplate = extractor._extract_simulation_template(
        session
    )

    yield simulation_template


@pytest.mark.asyncio
async def test_get_upload_instance():
    client = AsyncMock().return_value

    async def my_func(simulation_pk: int, offset: int, limit: int):
        rt = Mock()
        file = Mock()
        file.filename = "not_my_file_name"
        rt.results = [
            FileBoundaryCondition(id=1, simulation=1, state="processing", file=file),
        ]

        if offset >= 10:
            file2 = Mock()
            file2.filename = "my_file_name"
            rt.results.append(
                FileBoundaryCondition(
                    id=1, simulation=1, state="processing", file=file2
                )
            )

        rt.next = "http://url_to_next/"
        return rt

    api_func = client.simulations_events_boundaryconditions_file_list = my_func
    found = await get_upload_instance(api_func, 1, "my_file_name")

    assert (
        isinstance(found, FileBoundaryCondition)
        and found.file.filename == "my_file_name"
    )


@pytest.mark.asyncio
async def test_save_to_api(
    client: AsyncMock,
    upload_file_m: AsyncMock,
    simulation: Simulation,
    simulation_template,
):
    # Mock API functions called by the periodic (validation) state check
    client.simulations_events_lateral_file_read.return_value = FileLateral(
        id=10, simulation=1, offset=10, file=None, state="valid"
    )
    client.simulations_events_boundaryconditions_file_read.return_value = (
        FileBoundaryCondition(id=11, simulation=1, file=None, state="valid")
    )
    client.simulations_events_structure_control_file_read.return_value = (
        FileStructureControl(id=12, simulation=1, offset=9, file=None, state="valid")
    )

    initial_waterlevels = mock.Mock()
    initial_waterlevels.results = [
        InitialWaterlevel(id=11, source_raster_id=1, dimension="two_d"),
        InitialWaterlevel(id=12, source_raster_id=2, dimension="two_d"),
        InitialWaterlevel(id=13, dimension="one_d"),
    ]

    rasters = mock.Mock()
    rasters.results = [
        Raster(id=1, name="raster.tif", type="initial_waterlevel_file"),
        Raster(id=2, name="raster2.tif", type="initial_groundwater_level_file"),
    ]

    client.threedimodels_initial_waterlevels_list.return_value = initial_waterlevels
    client.threedimodels_rasters_list.return_value = rasters

    await simulation_template.save_to_api(client, "my_template", simulation)

    # Settings
    assert client.simulations_settings_numerical_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": simulation_template.settings.numerical,
    }
    assert client.simulations_settings_physical_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": simulation_template.settings.physical,
    }
    assert client.simulations_settings_time_step_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": simulation_template.settings.timestep,
    }
    assert client.simulations_settings_aggregation_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": simulation_template.settings.aggregations[0],
    }

    # Initials (based on specified, misses some calls)
    assert client.simulations_initial1d_water_level_file_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": simulation_template.initial_waterlevels.waterlevel_1d_file,
    }
    assert client.simulations_initial2d_water_level_raster_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": simulation_template.initial_waterlevels.raster_2d,
    }

    # Laterals
    assert client.simulations_events_lateral_file_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        # Need to check with the filename including the uuid4.hex()[:8]
        "data": UploadEventFile(
            filename=client.simulations_events_lateral_file_create.await_args.kwargs[
                "data"
            ].filename,
            offset=0,
        ),
    }

    # Boundaries
    assert client.simulations_events_boundaryconditions_file_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": UploadEventFile(
            filename=client.simulations_events_boundaryconditions_file_create.await_args.kwargs[
                "data"
            ].filename,
            offset=0,
        ),
    }

    # Structure controls
    assert client.simulations_events_structure_control_file_create.await_args.kwargs == {
        "simulation_pk": simulation.id,
        "data": UploadEventFile(
            filename=client.simulations_events_structure_control_file_create.await_args.kwargs[
                "data"
            ].filename,
            offset=0,
        ),
    }

    #  laterals, boundaries and structure controls file uploads
    assert upload_file_m.call_count == 3


@pytest.mark.asyncio
async def test_invalid_laterals(
    client: AsyncMock,
    upload_file_m: AsyncMock,
    simulation: Simulation,
    simulation_template,
):
    # API functions called by the periodic (validation) state check
    client.simulations_events_lateral_file_read.return_value = FileLateral(
        id=10, simulation=1, offset=10, file=None, state="invalid"
    )
    client.simulations_events_boundaryconditions_file_read.return_value = (
        FileBoundaryCondition(id=11, simulation=1, file=None, state="valid")
    )
    client.simulations_events_structure_control_file_read.return_value = (
        FileStructureControl(id=12, simulation=1, offset=9, file=None, state="valid")
    )

    with pytest.raises(TemplateValidationError):
        await simulation_template.save_to_api(client, "my_template", simulation)


@pytest.mark.parametrize(
    "lateral_state, boundary_state, control_state",
    [
        ("invalid", "valid", "valid"),
        ("valid", "invalid", "valid"),
        ("valid", "valid", "invalid"),
    ],
)
@pytest.mark.asyncio
async def test_invalid_boundaries(
    client: AsyncMock,
    upload_file_m: AsyncMock,
    simulation: Simulation,
    simulation_template,
    lateral_state,
    boundary_state,
    control_state,
):
    # API functions called by the periodic (validation) state check
    client.simulations_events_lateral_file_read.return_value = FileLateral(
        id=10, simulation=1, offset=10, file=None, state=lateral_state
    )
    client.simulations_events_boundaryconditions_file_read.return_value = (
        FileBoundaryCondition(id=11, simulation=1, file=None, state=boundary_state)
    )
    client.simulations_events_structure_control_file_read.return_value = (
        FileStructureControl(
            id=12, simulation=1, offset=9, file=None, state=control_state
        )
    )

    with pytest.raises(TemplateValidationError):
        await simulation_template.save_to_api(client, "my_template", simulation)


def test_simulation_template_extractor(session):
    num_settings = factories.NumericalSettingsFactory.create(id=1)
    global_settings = factories.GlobalSettingsFactory.create(
        id=1, numerical_settings_id=num_settings.id
    )
    factories.AggregationSettingsFactory.create(global_settings_id=global_settings.id)
    extractor = SimulationTemplateExtractor(Path("/tmp/nothing.sqlite"))

    simulation_template: SimulationTemplate = extractor._extract_simulation_template(
        session
    )

    assert isinstance(simulation_template, SimulationTemplate)


def test_boundary_conditions(session):
    for i in range(1, 3):
        factories.BoundaryConditions2DFactory.create(timeseries=f"0,-0.{i}\n1,-0.{i+1}")

    for i in range(3, 5):
        factories.BoundaryConditions1DFactory.create(timeseries=f"0,-0.{i}\n1,-0.{i+1}")

    extractor = BoundariesExtractor(session)
    values_check = [x["values"] for x in extractor.as_list()]
    assert values_check == [
        [[0, -0.1], [60, -0.2]],
        [[0, -0.2], [60, -0.3]],
        [[0, -0.3], [60, -0.4]],
        [[0, -0.4], [60, -0.5]],
    ]


def test_boundary_conditions_incorrect_timeseries(session):
    factories.BoundaryConditions1DFactory.create(timeseries="0;-0.1")
    extractor = BoundariesExtractor(session)

    with pytest.raises(SchematisationError):
        extractor.as_list()


def test_initial_waterlevels(session):
    global_settings = factories.GlobalSettingsFactory.create(
        initial_waterlevel=-10,
        initial_waterlevel_file="test.tif",
        water_level_ini_type=InitializationType.MAX,
        initial_groundwater_level=-12,
    )

    extractor = InitialWaterlevelExtractor(
        session, global_settings_id=global_settings.id
    )

    check = InitialWaterlevels(
        constant_2d=None,
        constant_1d=OneDWaterLevel(value=-10.0),
        constant_gw=GroundWaterLevel(value=-12.0),
        waterlevel_1d_file=None,
        raster_2d=TwoDWaterRaster(
            aggregation_method="max", initial_waterlevel="test.tif"
        ),
        raster_gw=None,
    )

    assert extractor.all_initial_waterlevels() == check

    # Check constant 1d override by connection nodes
    factories.ConnectionNodeFactory.create(initial_waterlevel=10)

    extractor = InitialWaterlevelExtractor(
        session, global_settings_id=global_settings.id
    )

    check.constant_1d = None
    check.waterlevel_1d_file = OneDWaterLevelFile(
        initial_waterlevel="resolved_during_saving"
    )

    assert extractor.all_initial_waterlevels() == check


def test_laterals(session):
    factories.Lateral1dFactory.create()
    factories.Lateral2DFactory.create()

    extractor = LateralsExtractor(session)

    to_check = [
        Lateral(
            **{
                "offset": 0,
                "interpolate": False,
                "values": [[0, -0.2]],
                "units": "m3/s",
                "point": {"type": "point", "coordinates": [-71.064544, 42.28787]},
            }
        ),
        Lateral(
            **{
                "offset": 0,
                "interpolate": False,
                "values": [[0, -0.1]],
                "units": "m3/s",
                "connection_node": 1,
            }
        ),
    ]
    all_laterals = extractor.all_laterals()
    to_check[1].connection_node = all_laterals[1].connection_node
    to_check[0].point = all_laterals[0].point
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
    global_settings = factories.GlobalSettingsFactory.create(
        id=1, numerical_settings_id=num_settings.id
    )
    factories.AggregationSettingsFactory.create(global_settings_id=global_settings.id)
    extractor = SettingsExtractor(session, global_settings_id=global_settings.id)

    to_check = Settings(
        numerical=NumericalSettings(
            **{
                "cfl_strictness_factor_1d": 1.0,
                "cfl_strictness_factor_2d": 1.0,
                "convergence_cg": 1e-09,
                "convergence_eps": 1e-05,
                "flooding_threshold": 0.01,
                "flow_direction_threshold": 1e-05,
                "friction_shallow_water_depth_correction": 0,
                "general_numerical_threshold": 1e-08,
                "limiter_slope_crossectional_area_2d": 0,
                "limiter_slope_friction_2d": 0,
                "limiter_slope_thin_water_layer": 0.01,
                "limiter_waterlevel_gradient_1d": 1,
                "limiter_waterlevel_gradient_2d": 1,
                "max_degree_gauss_seidel": 1,
                "max_non_linear_newton_iterations": 20,
                "min_friction_velocity": 0.01,
                "min_surface_area": 1e-08,
                "preissmann_slot": 0.0,
                "pump_implicit_ratio": 1.0,
                "time_integration_method": 0,
                "use_nested_newton": False,
                "use_of_cg": 20,
                "use_preconditioner_cg": 1,
            },
        ),
        physical=PhysicalSettings(
            **{"use_advection_1d": 1, "use_advection_2d": 1},
        ),
        timestep=TimeStepSettings(
            **{
                "max_time_step": 1.0,
                "min_time_step": 0.01,
                "output_time_step": 1.0,
                "time_step": 30.0,
                "use_time_step_stretch": False,
            }
        ),
        aggregations=[
            AggregationSettings(
                method="avg", flow_variable="water_level", interval=10.0
            )
        ],
    )

    assert extractor.all_settings() == to_check


def test_structure_controls(session, measure_group):
    control_group: ControlGroup = factories.ControlGroupFactory.create(
        id=1, name="test group"
    )
    table_control: ControlTable = factories.ControlTableFactory.create(id=1)
    memory_control: ControlMemory = factories.ControlMemoryFactory.create(id=1)
    timed_control: ControlTimed = factories.ControlTimedFactory.create(id=1)

    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=measure_group.id,
        control_type="table",
        control_id=table_control.id,
    )
    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=measure_group.id,
        control_type="memory",
        control_id=memory_control.id,
    )
    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=None,
        control_type="timed",
        control_id=timed_control.id,
    )

    extractor = StructureControlExtractor(session, control_group_id=control_group.id)

    to_check = StructureControls.from_dict(
        {
            "memory": [
                {
                    "offset": 0,
                    "duration": 300,
                    "measure_specification": {
                        "name": "test group",
                        "locations": [
                            {
                                "weight": "0.1",
                                "content_type": "v2_connection_node",
                                "content_pk": 101,
                            }
                        ],
                        "variable": "s1",
                        "operator": ">",
                    },
                    "structure_id": 10,
                    "structure_type": "v2_channel",
                    "type": "set_discharge_coefficients",
                    "value": [0.0, -1.0],
                    "upper_threshold": 1.0,
                    "lower_threshold": -1.0,
                    "is_active": True,
                    "is_inverse": False,
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
                                "weight": "0.1",
                                "content_type": "v2_connection_node",
                                "content_pk": 101,
                            }
                        ],
                        "variable": "s1",
                        "operator": ">",
                    },
                    "structure_id": 10,
                    "structure_type": "v2_channel",
                    "type": "set_discharge_coefficients",
                    "values": [[0.0, -1.0]],
                }
            ],
            "timed": [
                {
                    "offset": 0,
                    "duration": 300,
                    "value": [0.0, -1.0],
                    "type": "set_discharge_coefficients",
                    "structure_id": 10,
                    "structure_type": "v2_channel",
                }
            ],
        }
    )

    assert extractor.all_controls().as_dict() == to_check.as_dict()


def test_table_control_incorrect_timeseries(session, measure_group):
    control_group: ControlGroup = factories.ControlGroupFactory.create(
        id=1, name="test group"
    )
    table_control: ControlTable = factories.ControlTableFactory.create(
        id=1, action_table="0.0,-1.0"
    )

    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=measure_group.id,
        control_type="table",
        control_id=table_control.id,
    )

    extractor = StructureControlExtractor(session, control_group_id=control_group.id)

    with pytest.raises(SchematisationError):
        extractor.all_controls()


def test_memory_control_incorrect_timeseries(session, measure_group):
    control_group: ControlGroup = factories.ControlGroupFactory.create(
        id=1, name="test group"
    )
    memory_control: ControlMemory = factories.ControlMemoryFactory.create(
        id=1, action_value="0.0;1.0"
    )
    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=measure_group.id,
        control_type="memory",
        control_id=memory_control.id,
    )

    extractor = StructureControlExtractor(session, control_group_id=control_group.id)

    with pytest.raises(SchematisationError):
        extractor.all_controls()


def test_timed_control_incorrect_timeseries(session, measure_group):
    control_group: ControlGroup = factories.ControlGroupFactory.create(
        id=1, name="test group"
    )
    timed_control: ControlTimed = factories.ControlTimedFactory.create(
        id=1, action_table="0.0,1.0"
    )

    factories.ControlFactory.create(
        control_group_id=control_group.id,
        measure_group_id=None,
        control_type="timed",
        control_id=timed_control.id,
    )

    extractor = StructureControlExtractor(session, control_group_id=control_group.id)

    with pytest.raises(SchematisationError):
        extractor.all_controls()
