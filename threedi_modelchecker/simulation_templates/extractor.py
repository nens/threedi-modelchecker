from .exceptions import SchematisationError
from pathlib import Path
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session
from datetime import datetime, timezone
from threedi_modelchecker.simulation_templates.boundaries.extractor import (
    BoundariesExtractor,
)
from threedi_modelchecker.simulation_templates.initial_waterlevels.extractor import (
    InitialWaterlevelExtractor,
)
from threedi_modelchecker.simulation_templates.laterals.dwf_calculator import (
    DWFCalculator,
)
from threedi_modelchecker.simulation_templates.laterals.extractor import (
    LateralsExtractor,
)
from threedi_modelchecker.simulation_templates.models import Events
from threedi_modelchecker.simulation_templates.models import (
    GlobalSettingOption,
)
from threedi_modelchecker.simulation_templates.models import SimulationTemplate
from threedi_modelchecker.simulation_templates.settings.extractor import (
    SettingsExtractor,
)
from threedi_modelchecker.simulation_templates.structure_controls.extractor import (
    StructureControlExtractor,
)
from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.threedi_model.models import GlobalSetting
from typing import List
from typing import Optional


__all__ = ["SimulationTemplateExtractor"]


def parse_datetime(global_setting: GlobalSetting) -> Optional[datetime]:
    # first try combination, than start_time than start_date
    for option in [
        global_setting.start_date + " " + global_setting.start_time,
        global_setting.start_time,
        global_setting.start_date,
    ]:
        try:
            dt = datetime.fromisoformat(option)
        except (ValueError, TypeError):
            dt = None
        if dt:
            dt = dt.astimezone(timezone.utc)
            break

    return dt


def get_duration(global_setting: GlobalSetting) -> Optional[int]:
    try:
        duration = int(global_setting.nr_timesteps) * int(global_setting.sim_time_step)
    except (ValueError, TypeError):
        duration = None
    return duration


class SimulationTemplateExtractor(object):
    def __init__(self, sqlite_path: Path):
        """
        param global_settings_id: if None the first global setting entry is taken (default)
        """
        self.sqlite_path = sqlite_path
        self.database = ThreediDatabase(
            connection_settings={"db_path": self.sqlite_path.as_posix()},
            db_type="spatialite",
        )

    def _extract_simulation_template(
        self, session: Session, global_settings_id: Optional[int] = None
    ) -> SimulationTemplate:
        """
        Extract a SimulationTemplate instance using the given database session
        """
        qr = Query(GlobalSetting).with_session(session)
        if global_settings_id is not None:
            qr = qr.filter(GlobalSetting.id == global_settings_id)
        global_settings: GlobalSetting = qr.first()

        if global_settings is None:
            raise SchematisationError(
                f"Global settings with id: {global_settings_id} not found."
            )

        dwf_laterals = DWFCalculator(session, global_settings.use_0d_inflow).laterals
        initial_waterlevels = InitialWaterlevelExtractor(session, global_settings_id)
        settings = SettingsExtractor(session, global_settings.id)

        return SimulationTemplate(
            events=Events(
                structure_controls=StructureControlExtractor(
                    session, control_group_id=global_settings.control_group_id
                ).all_controls(),
                laterals=LateralsExtractor(session).as_list(),
                dwf_laterals=dwf_laterals,
                boundaries=BoundariesExtractor(session).as_list(),
            ),
            settings=settings.all_settings(),
            initial_waterlevels=initial_waterlevels.all_initial_waterlevels(),
        )

    def _get_global_settings_options(
        self, session: Session
    ) -> List[GlobalSettingOption]:
        return [
            GlobalSettingOption(x.id, x.name, parse_datetime(x), get_duration(x))
            for x in Query(GlobalSetting).with_session(session)
        ]

    def global_settings_options(self) -> List[GlobalSettingOption]:
        try:
            session = self.database.get_session()
            return self._get_global_settings_options(session)
        finally:
            session.close()

    def extract(self, global_settings_id: Optional[int] = None) -> SimulationTemplate:
        """
        Return simulation template for
        """
        try:
            session = self.database.get_session()
            return self._extract_simulation_template(session, global_settings_id)
        finally:
            session.close()
