from typing import Optional
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session
from threedi_api_client.openapi.models.ground_water_level import GroundWaterLevel
from threedi_api_client.openapi.models.one_d_water_level_predefined import (
    OneDWaterLevelPredefined,
)
from threedi_api_client.openapi.models.two_d_water_level import TwoDWaterLevel
from threedi_api_client.openapi.models import TwoDWaterRaster, GroundWaterRaster
from threedi_api_client.openapi.models import OneDWaterLevel
from threedi_modelchecker.simulation_templates.models import InitialWaterlevels
from threedi_modelchecker.threedi_model.models import ConnectionNode, GlobalSetting

sqlite_agg_method_to_api_map = {0: "max", 1: "min", 2: "mean"}


class InitialWaterlevelExtractor(object):
    def __init__(self, session: Session, global_settings_id: Optional[int] = None):
        self.session = session
        self._global_settings = None
        self._global_settings_id = global_settings_id
        self._connection_nodes_with_initial_waterlevels = None

    @property
    def has_connection_nodes_with_initial_waterlevels(self) -> bool:
        if self._connection_nodes_with_initial_waterlevels is None:
            self._connection_nodes_with_initial_waterlevels = (
                Query(ConnectionNode)
                .with_session(self.session)
                .filter(ConnectionNode.initial_waterlevel != None)
                .first()
                is not None
            )
        return self._connection_nodes_with_initial_waterlevels

    @property
    def global_settings(self) -> GlobalSetting:
        if self._global_settings is None:
            qr = Query(GlobalSetting).with_session(self.session)
            if self._global_settings_id is not None:
                qr = qr.filter(GlobalSetting.id == self._global_settings_id)
            self._global_settings = qr.first()
        return self._global_settings

    @property
    def constant_waterlevel_1d(self) -> Optional[OneDWaterLevel]:
        if self.global_settings.initial_waterlevel is None:
            return None
        if self.has_connection_nodes_with_initial_waterlevels:
            return None
        if float(self.global_settings.initial_waterlevel) == -9999:
            return None
        return OneDWaterLevel(value=float(self.global_settings.initial_waterlevel))

    @property
    def constant_waterlevel_2d(self) -> Optional[TwoDWaterLevel]:
        if self.global_settings.initial_waterlevel is None:
            return None
        if self.global_settings.initial_waterlevel_file is not None:
            return None
        if float(self.global_settings.initial_waterlevel) == -9999:
            return None
        return TwoDWaterLevel(value=float(self.global_settings.initial_waterlevel))

    @property
    def constant_waterlevel_groundwater(self) -> Optional[GroundWaterLevel]:
        if self.global_settings.initial_groundwater_level is None:
            return None
        if float(self.global_settings.initial_groundwater_level) == -9999:
            return None
        return GroundWaterLevel(
            value=float(self.global_settings.initial_groundwater_level)
        )

    @property
    def predefined_1d(self) -> Optional[OneDWaterLevelPredefined]:
        if not self.has_connection_nodes_with_initial_waterlevels:
            return None
        return OneDWaterLevelPredefined()

    @property
    def waterlevel_2d_raster(self) -> Optional[TwoDWaterRaster]:
        if (
            self.global_settings.initial_waterlevel_file is None
            or self.global_settings.water_level_ini_type is None
        ):
            return None
        return TwoDWaterRaster(
            aggregation_method=sqlite_agg_method_to_api_map[
                self.global_settings.water_level_ini_type.value
            ],
            initial_waterlevel=self.global_settings.initial_waterlevel_file,
        )

    @property
    def waterlevel_groundwater_raster(self) -> Optional[GroundWaterRaster]:
        if (
            self.global_settings.initial_groundwater_level_file is None
            or self.global_settings.initial_groundwater_level_type is None
        ):
            return None
        return GroundWaterRaster(
            aggregation_method=sqlite_agg_method_to_api_map[
                self.global_settings.initial_groundwater_level_type.value
            ],
            initial_waterlevel=self.global_settings.initial_groundwater_level_file,
        )

    def all_initial_waterlevels(self) -> InitialWaterlevels:
        return InitialWaterlevels(
            self.constant_waterlevel_2d,
            self.constant_waterlevel_1d,
            self.constant_waterlevel_groundwater,
            self.predefined_1d,
            self.waterlevel_2d_raster,
            self.waterlevel_groundwater_raster,
        )
