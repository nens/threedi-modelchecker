from enum import Enum
import json
from io import BytesIO
import asyncio
from dataclasses import dataclass, fields, InitVar
from uuid import uuid4
from typing import Dict, List, Optional, Any
from threedi_api_client.openapi.models import TimeStepSettings
from threedi_api_client.openapi.models import PhysicalSettings
from threedi_api_client.openapi.models import NumericalSettings, AggregationSettings
from threedi_api_client.openapi.models import Lateral, FileLateral
from threedi_api_client.openapi.models import (
    TableStructureControl,
    MemoryStructureControl,
    TimedStructureControl,
    MeasureSpecification,
    MeasureLocation,
)
from threedi_api_client.openapi.models.file_boundary_condition import (
    FileBoundaryCondition,
)
from threedi_api_client.openapi.models.file_structure_control import (
    FileStructureControl,
)
from threedi_api_client.openapi.models.ground_water_level import GroundWaterLevel
from threedi_api_client.openapi.models.ground_water_raster import GroundWaterRaster
from threedi_api_client.openapi.models.one_d_water_level import OneDWaterLevel
from threedi_api_client.openapi.models.one_d_water_level_predefined import (
    OneDWaterLevelPredefined,
)
from threedi_api_client.openapi.models.two_d_water_level import TwoDWaterLevel
from threedi_api_client.openapi.models.two_d_water_raster import TwoDWaterRaster
from threedi_modelchecker.simulation_templates.utils import strip_dict_none_values
from threedi_api_client.openapi.models import Simulation, UploadEventFile, Template
from threedi_api_client.versions import V3BetaApi
from threedi_api_client.aio.files import upload_fileobj
from .exceptions import TemplateValidationError, TemplateValidationTimeoutError


__all__ = [
    "ValidationStatus",
    "GlobalSettingOption",
    "InitialWaterlevels",
    "StructureControls",
    "Settings",
    "Events",
    "SimulationTemplate",
]


class ValidationStatus(Enum):
    processing: str = "processing"
    valid: str = "valid"
    invalid: str = "invalid"


@dataclass
class GlobalSettingOption:
    """
    Derived global setting option from v2_global_settings table
    """

    id: int  # v2_global_settings.id
    name: str


class AsyncBytesIO:
    """
    Simple wrapper class to make BytesIO async
    """

    def __init__(self, bytes_io: BytesIO):
        self._bytes_io = bytes_io

    async def seek(self, *args, **kwargs):
        return self._bytes_io.seek(*args, **kwargs)

    async def read(self, *args, **kwargs):
        return self._bytes_io.read(*args, **kwargs)


async def get_upload_instance(
    api_func, simulation_pk: int, filename: str
) -> Optional[Any]:
    """
    Get the uploaded file instance based on filename

    api_func should be an async API function to list a
    file upload instance
    """
    offset: int = 0
    limit: int = 10

    found = None
    next: bool = True

    while not found and next:
        res = await api_func(simulation_pk=simulation_pk, offset=offset, limit=limit)
        results = [x for x in res.results if x.file.filename == filename]

        if results:
            found = results[0]
            break

        # Make sure AsyncMock used in unit-tests are not evaluated as true
        next = res.next is not None and isinstance(res.next, str) and len(res.next) != 0
        offset += 10
        limit += 10

    return found


def openapi_to_dict(value: Any):
    """
    Convert openapi object to Dict
    """
    if hasattr(value, "openapi_types") and hasattr(value, "to_dict"):
        value = value.to_dict()
        strip_dict_none_values(value)
    return value


class AsDictMixin:
    def as_dict(self) -> Dict:
        """
        Convert fields to dictionary
        """
        rt = {}
        for field_name in [x.name for x in fields(self)]:
            value = getattr(self, field_name)
            if isinstance(value, AsDictMixin):
                value = value.as_dict()
            elif isinstance(value, list):
                value = [openapi_to_dict(x) for x in value]
            else:
                value = openapi_to_dict(value)
            rt[field_name] = value
        return rt


@dataclass
class InitialWaterlevels(AsDictMixin):
    constant_2d: Optional[TwoDWaterLevel] = None
    constant_1d: Optional[OneDWaterLevel] = None
    constant_gw: Optional[GroundWaterLevel] = None
    predefined_1d: Optional[OneDWaterLevelPredefined] = None
    raster_2d: Optional[TwoDWaterRaster] = None
    raster_gw: Optional[GroundWaterRaster] = None

    _validation_status: InitVar[ValidationStatus] = ValidationStatus.processing

    async def is_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        return self._validation_status

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save initial waterlevels to the API on the given simulation
        """
        if self._validation_status == ValidationStatus.valid:
            # Already saved
            return

        self._validation_status == ValidationStatus.processing

        tasks = []
        if self.constant_1d is not None:
            tasks.append(
                client.simulations_initial1d_water_level_constant_create(
                    simulation_pk=simulation.id, data=self.constant_1d
                )
            )
        if self.constant_2d is not None:
            tasks.append(
                client.simulations_initial2d_water_level_constant_create(
                    simulation_pk=simulation.id, data=self.constant_2d
                )
            )
        if self.constant_gw is not None:
            tasks.append(
                client.simulations_initial_groundwater_level_constant_create(
                    simulation_pk=simulation.id, data=self.constant_gw
                )
            )
        if self.predefined_1d is not None:
            tasks.append(
                client.simulations_initial1d_water_level_predefined_create(
                    simulation_pk=simulation.id, data=self.predefined_1d
                )
            )

        # TODO: figure out 2D and GW rasters, probably these need to
        # be processed in a seperate worker before adding them here

        if tasks:
            await asyncio.gather(*tasks)

        self._validation_status = ValidationStatus.valid

    @classmethod
    def from_dict(cls, dict: Dict) -> "InitialWaterlevels":
        map = {
            "constant_2d": TwoDWaterLevel,
            "constant_1d": OneDWaterLevel,
            "constant_gw": GroundWaterLevel,
            "predefined_1d": OneDWaterLevelPredefined,
            "raster_2d": TwoDWaterRaster,
            "raster_gw": GroundWaterRaster,
        }

        data = {}
        for key, klass in map.items():
            data[key] = None if dict[key] is None else klass(**dict[key])

        return InitialWaterlevels(**data)


@dataclass
class StructureControls(AsDictMixin):
    memory: List[MemoryStructureControl]
    table: List[TableStructureControl]
    timed: List[TimedStructureControl]

    _controls_upload: InitVar[Optional[FileStructureControl]] = None
    _validation_status: InitVar[Optional[ValidationStatus]] = None
    _simulation: InitVar[Optional[Simulation]] = None

    async def is_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        """
        Return ValidationStatus of uploaded controls file
        """
        if self._controls_upload is None:
            return ValidationStatus.valid

        if ValidationStatus[self._controls_upload.state] == ValidationStatus.processing:
            # Refresh from API
            self._controls_upload: FileStructureControl = (
                await client.simulations_events_structure_control_file_read(
                    id=self._controls_upload.id, simulation_pk=self._simulation.id
                )
            )

        validation_status: ValidationStatus = ValidationStatus[
            self._controls_upload.state
        ]

        if validation_status == ValidationStatus.invalid:
            raise TemplateValidationError(
                f"Provided structure controls could not be validated succesfully, {self._controls_upload.state_detail}"
            )

        return validation_status

    @classmethod
    def from_dict(cls, dict: Dict) -> "StructureControls":
        def convert_measure_specs(data: Dict):
            """
            Convert measure specification on tables/memory from dict to OpenAPI models
            """
            rt = {}
            for k, v in data.items():
                if k == "measure_specification":
                    v = MeasureSpecification(**data[k])
                    v.locations = [MeasureLocation(**x) for x in data[k]["locations"]]

                rt[k] = v
            return rt

        return StructureControls(
            memory=[
                MemoryStructureControl(**convert_measure_specs(x))
                for x in dict["memory"]
            ],
            table=[
                TableStructureControl(**convert_measure_specs(x)) for x in dict["table"]
            ],
            timed=[TimedStructureControl(**x) for x in dict["timed"]],
        )

    @property
    def has_controls(self) -> bool:
        return len(self.memory) + len(self.table) + len(self.timed) > 0

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save structure controls to API on the given simulation

        Saves them individual if the total count <= 30, else saves
        them using file upload.
        """
        self._simulation = simulation

        if not self.has_controls:
            return

        data: Dict = {"memory": [], "table": [], "timed": []}
        for memory_control in self.memory:
            data["memory"].append(openapi_to_dict(memory_control))
        for table_control in self.table:
            data["table"].append(openapi_to_dict(table_control))
        for timed_control in self.timed:
            data["timed"].append(openapi_to_dict(timed_control))

        filename: str = f"controls{uuid4().hex[0:8]}.json"

        upload: UploadEventFile = (
            await client.simulations_events_structure_control_file_create(
                simulation_pk=simulation.id,
                data=UploadEventFile(filename="structure_controls.json", offset=0),
            )
        )

        await upload_fileobj(
            upload.put_url, AsyncBytesIO(BytesIO(json.dumps(data).encode()))
        )

        # Try to find structure control resource
        controls_upload: Optional[FileStructureControl] = await get_upload_instance(
            client.simulations_events_structure_control_file_list,
            simulation.id,
            filename,
        )

        if controls_upload is None:
            raise TemplateValidationError(
                "Could not find uploaded structure controls file resource"
            )
        self._controls_upload = controls_upload


@dataclass
class Settings(AsDictMixin):
    numerical: NumericalSettings
    physical: PhysicalSettings
    timestep: TimeStepSettings
    aggregations: List[AggregationSettings]
    _validation_status: InitVar[ValidationStatus] = ValidationStatus.processing

    async def is_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        return self._validation_status

    @classmethod
    def from_dict(cls, dict: Dict) -> "Settings":
        return Settings(
            numerical=NumericalSettings(**dict["numerical"]),
            physical=PhysicalSettings(**dict["physical"]),
            timestep=TimeStepSettings(**dict["timestep"]),
            aggregations=[AggregationSettings(**x) for x in dict["aggregations"]],
        )

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save settings to API on given simulation
        """
        if self._validation_status == ValidationStatus.valid:
            # Already saved
            return

        self._validation_status = ValidationStatus.processing

        tasks = [
            client.simulations_settings_numerical_create(
                simulation_pk=simulation.id, data=self.numerical
            ),
            client.simulations_settings_physical_create(
                simulation_pk=simulation.id, data=self.physical
            ),
            client.simulations_settings_time_step_create(
                simulation_pk=simulation.id, data=self.timestep
            ),
        ]
        for aggregation in self.aggregations:
            tasks.append(
                client.simulations_settings_aggregation_create(
                    simulation_pk=simulation.id, data=aggregation
                )
            )

        # Add aggregations
        await asyncio.gather(*tasks)

        self._validation_status = ValidationStatus.valid


@dataclass
class Events(AsDictMixin):
    laterals: List[Lateral]
    boundaries: List[Dict]
    structure_controls: StructureControls

    _validation_status: InitVar[Optional[ValidationStatus]] = None
    _lateral_upload: InitVar[Optional[FileLateral]] = None
    _boundary_upload: InitVar[Optional[FileBoundaryCondition]] = None

    # Simulation used to store events
    _simulation: InitVar[Optional[Simulation]] = None

    async def _is_laterals_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        """
        Return ValidationStatus of uploaded lateral file
        """
        if self._lateral_upload is None:
            return ValidationStatus.valid

        if ValidationStatus[self._lateral_upload.state] == ValidationStatus.processing:
            # Refresh from API
            self._lateral_upload: FileLateral = (
                await client.simulations_events_lateral_file_read(
                    id=self._lateral_upload.id, simulation_pk=self._simulation.id
                )
            )

        validation_status: ValidationStatus = ValidationStatus[
            self._lateral_upload.state
        ]

        if validation_status == ValidationStatus.invalid:
            raise TemplateValidationError(
                f"Provided laterals could not be validated succesfully, {self._lateral_upload.state_detail}"
            )

        return validation_status

    async def _is_boundaries_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        """
        Return ValidationStatus of uploaded boundary file
        """
        if self._boundary_upload is None:
            return ValidationStatus.valid

        if ValidationStatus[self._boundary_upload.state] == ValidationStatus.processing:
            # Refresh from API
            self._boundary_upload: FileBoundaryCondition = (
                await client.simulations_events_boundaryconditions_file_read(
                    id=self._boundary_upload.id, simulation_pk=self._simulation.id
                )
            )

        validation_status: ValidationStatus = ValidationStatus[
            self._boundary_upload.state
        ]

        if validation_status == ValidationStatus.invalid:
            raise TemplateValidationError(
                f"Provided laterals could not be validated succesfully, {self._boundary_upload.state_detail}"
            )

        return validation_status

    async def is_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        """
        Returns ValidationStatus (processing or valid) or raises TemplateValidationError in case
        something is invalid
        """
        if await self._is_laterals_valid_in_api(client) == ValidationStatus.processing:
            return ValidationStatus.processing

        if (
            await self._is_boundaries_valid_in_api(client)
            == ValidationStatus.processing
        ):
            return ValidationStatus.processing

        if (
            await self.structure_controls.is_valid_in_api(client)
            == ValidationStatus.processing
        ):
            return ValidationStatus.processing

        # If no errors have been raised, the validation is succesfully
        return ValidationStatus.valid

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save events to API on the given simulation
        """
        self._simulation = simulation

        tasks = [
            # Laterals
            self.save_laterals_to_api(client, simulation),
            # Boundaries
            self.save_boundaries_to_api(client, simulation),
            # Structure controls
            self.structure_controls.save_to_api(client, simulation),
        ]
        await asyncio.gather(*tasks)

    async def save_laterals_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        Save laterals to API on the given simulation as file upload.
        """

        if self._simulation is None:
            self._simulation = simulation

        if len(self.laterals) == 0:
            return

        data = [openapi_to_dict(x) for x in self.laterals]
        data = AsyncBytesIO(BytesIO(json.dumps(data).encode()))

        filename: str = f"laterals_{uuid4().hex[:8]}.json"

        upload: UploadEventFile = await client.simulations_events_lateral_file_create(
            simulation_pk=simulation.id,
            data=UploadEventFile(filename=filename, offset=0),
        )
        await upload_fileobj(upload.put_url, data)

        # Try to find lateral uploaded resource
        lateral_upload: Optional[FileLateral] = await get_upload_instance(
            client.simulations_events_lateral_file_list, simulation.id, filename
        )

        if lateral_upload is None:
            raise TemplateValidationError(
                "Could not find uploaded lateral file resource"
            )
        self._lateral_upload = lateral_upload

    async def save_boundaries_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        Save boundarie to API on the given simulation
        """
        if self._simulation is None:
            self._simulation = simulation

        if len(self.boundaries) == 0:
            return

        data = [openapi_to_dict(x) for x in self.boundaries]
        data = AsyncBytesIO(BytesIO(json.dumps(data).encode()))

        filename: str = f"boundaries_{uuid4().hex[:8]}.json"

        upload: UploadEventFile = (
            await client.simulations_events_boundaryconditions_file_create(
                simulation_pk=simulation.id,
                data=UploadEventFile(filename=filename, offset=0),
            )
        )
        await upload_fileobj(upload.put_url, data)

        # Try to find boundary uploaded resource
        boundary_upload: Optional[FileBoundaryCondition] = await get_upload_instance(
            client.simulations_events_boundaryconditions_file_list,
            simulation.id,
            filename,
        )

        if boundary_upload is None:
            raise TemplateValidationError(
                "Could not find uploaded boundary file resource"
            )

        self._boundary_upload = boundary_upload

    @classmethod
    def from_dict(cls, dict: Dict) -> "Events":
        return Events(
            laterals=[Lateral(**x) for x in dict["laterals"]],
            boundaries=dict["boundaries"],
            structure_controls=StructureControls.from_dict(dict["structure_controls"]),
        )


@dataclass
class SimulationTemplate(AsDictMixin):
    settings: Settings
    events: Events
    initial_waterlevels: InitialWaterlevels

    # if saved to api, the Simulation the data is saved to
    _simulation: InitVar[Optional[Simulation]] = None

    async def is_valid_in_api(self, client: V3BetaApi) -> ValidationStatus:
        """
        Check if all data for this SimulationTemplate has been saved correctly in the API

        returns:
            ValidationStatus.valid if everything is ok
            ValidationStatus.processing if still validating (or nothing saved)

        raises: TemplateValidationError in case of invalid data.
        """
        if await self.settings.is_valid_in_api(client) == ValidationStatus.processing:
            return ValidationStatus.processing

        if await self.events.is_valid_in_api(client) == ValidationStatus.processing:
            return ValidationStatus.processing

        if (
            await self.initial_waterlevels.is_valid_in_api(client)
            == ValidationStatus.processing
        ):
            return ValidationStatus.processing

        # All are valid (none is processing and no TemplateValidationError)
        return ValidationStatus.valid

    async def save_to_api(
        self,
        client: V3BetaApi,
        template_name: str,
        simulation: Simulation,
        timeout: int = 300,
    ) -> Template:

        if simulation.id is None:
            # Save Simulation
            simulation: Simulation = await client.simulations_create(data=simulation)

        self._simulation = simulation

        # Conditonally save things to simulation in the API,
        # if not done already
        await self.settings.save_to_api(client, simulation)
        await self.events.save_to_api(client, simulation)
        await self.initial_waterlevels.save_to_api(client, simulation)

        # Check validity of everything
        async def wait_for_validation(client: V3BetaApi) -> None:
            # increase sleep time, in steps to 8 sec
            SLEEPTIME: int = [2, 3, 5, 8]
            index: int = 0

            while await self.is_valid_in_api(client) == ValidationStatus.processing:
                if index < len(SLEEPTIME) - 2:
                    index += 1
                await asyncio.sleep(SLEEPTIME[index])

        try:
            await asyncio.wait_for(wait_for_validation(client), timeout=timeout)
        except TimeoutError:
            raise TemplateValidationTimeoutError(
                "Template validating timed out, please try again later."
            )

        # All things should be valid now, save template
        template: Template = await client.simulation_templates_create(
            data=Template(simulation=simulation.id, name=template_name)
        )
        return template

    @classmethod
    def from_dict(cls, dict: Dict) -> "SimulationTemplate":
        return SimulationTemplate(
            settings=Settings.from_dict(dict["settings"]),
            events=Events.from_dict(dict["events"]),
            initial_waterlevels=InitialWaterlevels.from_dict(
                dict["initial_waterlevels"]
            ),
        )
