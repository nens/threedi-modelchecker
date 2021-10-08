import json
from io import BytesIO
import asyncio
from dataclasses import dataclass, fields
from typing import Dict, List, Optional, Any
from threedi_api_client.openapi.models import TimeStepSettings
from threedi_api_client.openapi.models import PhysicalSettings
from threedi_api_client.openapi.models import NumericalSettings, AggregationSettings
from threedi_api_client.openapi.models import Lateral
from threedi_api_client.openapi.models import (
    TableStructureControl,
    MemoryStructureControl,
    TimedStructureControl,
    MeasureSpecification,
    MeasureLocation,
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
from threedi_api_client.openapi.models import Simulation, UploadEventFile
from threedi_api_client.versions import V3BetaApi
from threedi_api_client.aio.files import upload_fileobj


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

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save initial waterlevels to the API on the given simulation
        """
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

        # TODO: figure out rasters, probably these need to
        # be processed in a seperate worker before adding them here

        if tasks:
            await asyncio.gather(*tasks)

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
        if not self.has_controls:
            return

        data: Dict = {"memory": [], "table": [], "timed": []}
        for memory_control in self.memory:
            data["memory"].append(openapi_to_dict(memory_control))
        for table_control in self.table:
            data["table"].append(openapi_to_dict(table_control))
        for timed_control in self.timed:
            data["timed"].append(openapi_to_dict(timed_control))

        upload: UploadEventFile = (
            await client.simulations_events_structure_control_file_create(
                simulation_pk=simulation.id,
                data=UploadEventFile(filename="structure_controls.json", offset=0),
            )
        )

        await upload_fileobj(
            upload.put_url, AsyncBytesIO(BytesIO(json.dumps(data).encode()))
        )


@dataclass
class Settings(AsDictMixin):
    numerical: NumericalSettings
    physical: PhysicalSettings
    timestep: TimeStepSettings

    aggregations: List[AggregationSettings]

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


@dataclass
class Events(AsDictMixin):
    laterals: List[Lateral]
    boundaries: List[Dict]
    structure_controls: StructureControls

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save events to API on the given simulation
        """
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
        if len(self.laterals) == 0:
            return

        data = [openapi_to_dict(x) for x in self.laterals]
        data = AsyncBytesIO(BytesIO(json.dumps(data).encode()))

        upload: UploadEventFile = await client.simulations_events_lateral_file_create(
            simulation_pk=simulation.id,
            data=UploadEventFile(filename="laterals.json", offset=0),
        )
        await upload_fileobj(upload.put_url, data)

    async def save_boundaries_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        Save boundarie to API on the given simulation
        """
        if len(self.boundaries) == 0:
            return

        data = [openapi_to_dict(x) for x in self.boundaries]
        data = AsyncBytesIO(BytesIO(json.dumps(data).encode()))

        upload: UploadEventFile = (
            await client.simulations_events_boundaryconditions_file_create(
                simulation_pk=simulation.id,
                data=UploadEventFile(filename="boundaries.json", offset=0),
            )
        )
        await upload_fileobj(upload.put_url, data)

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

    async def save_to_api(self, client: V3BetaApi, simulation: Simulation):
        """
        :param: client = ThreediApi(async=True)

        Save this simulation-template data to the API on the given simulation
        """
        # Save events
        await self.events.save_to_api(client, simulation)

        # Save simulation settings
        await self.settings.save_to_api(client, simulation)

        # Save initial waterlevels
        await self.initial_waterlevels.save_to_api(client, simulation)

    @classmethod
    def from_dict(cls, dict: Dict) -> "SimulationTemplate":
        return SimulationTemplate(
            settings=Settings.from_dict(dict["settings"]),
            events=Events.from_dict(dict["events"]),
            initial_waterlevels=InitialWaterlevels.from_dict(
                dict["initial_waterlevels"]
            ),
        )
