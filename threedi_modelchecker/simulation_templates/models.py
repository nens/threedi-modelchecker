from dataclasses import dataclass, fields
from typing import Dict, List, Optional
from threedi_api_client.openapi.models import TimeStepSettings
from threedi_api_client.openapi.models import PhysicalSettings
from threedi_api_client.openapi.models import NumericalSettings, AggregationSettings
from threedi_api_client.openapi.models import Lateral
from threedi_api_client.openapi.models import TableStructureControl, MemoryStructureControl, TimedStructureControl
from threedi_api_client.openapi.models.ground_water_level import GroundWaterLevel
from threedi_api_client.openapi.models.ground_water_raster import GroundWaterRaster
from threedi_api_client.openapi.models.one_d_water_level import OneDWaterLevel
from threedi_api_client.openapi.models.one_d_water_level_predefined import OneDWaterLevelPredefined
from threedi_api_client.openapi.models.two_d_water_level import TwoDWaterLevel
from threedi_api_client.openapi.models.two_d_water_raster import TwoDWaterRaster
from threedi_modelchecker.simulation_templates.utils import strip_dict_none_values


def openapi_to_dict(value):
    if hasattr(value, 'openapi_types') and hasattr(value, 'to_dict'):
        value = value.to_dict()
        strip_dict_none_values(value)
    return value


class AsDictMixin:
    def as_dict(self) -> Dict:
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
    constant_gw: Optional[GroundWaterLevel] =  None
    predefined_1d: Optional[OneDWaterLevelPredefined] = None
    raster_2d: Optional[TwoDWaterRaster] = None
    raster_gw: Optional[GroundWaterRaster] = None

    @classmethod
    def from_dict(cls, dict: Dict) -> "InitialWaterlevels":
        map = {
            "constant_2d": TwoDWaterLevel,
            "constant_1d": OneDWaterLevel,
            "constant_gw": GroundWaterLevel,
            "predefined_1d": OneDWaterLevelPredefined,
            "raster_2d": TwoDWaterRaster,
            "raster_gw": GroundWaterRaster
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
        return StructureControls(
            memory=[MemoryStructureControl(**x) for x in dict["memory"]],
            table=[TableStructureControl(**x) for x in dict["table"]],
            timed=[TimedStructureControl(**x) for x in dict["timed"]]
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

@dataclass
class Events(AsDictMixin):
    laterals: List[Lateral]
    boundaries: List[Dict]
    structure_controls: StructureControls

    @classmethod
    def from_dict(cls, dict: Dict) -> "Events":
        return Events(
            laterals=[Lateral(**x) for x in dict["laterals"]],
            boundaries=dict["boundaries"],
            structure_controls=StructureControls.from_dict(dict["structure_controls"])
        )


@dataclass
class SimulationTemplate(AsDictMixin):
    settings: Settings
    events: Events
    initial_waterlevels: InitialWaterlevels
        
    @classmethod
    def from_dict(cls, dict: Dict) -> "SimulationTemplate":
        return SimulationTemplate(
            settings=Settings.from_dict(dict["settings"]),
            events=Events.from_dict(dict["events"]),
            initial_waterlevels=InitialWaterlevels.from_dict(dict["initial_waterlevels"]),
        )