from pathlib import Path
from typing import Optional

from sqlalchemy.orm.session import Session
from threedi_modelchecker.simulation_templates.initial_waterlevels.extractor import (
    InitialWaterlevelExtractor,
)
from threedi_modelchecker.simulation_templates.laterals.extractor import (
    LateralsExtractor,
)
from threedi_modelchecker.simulation_templates.boundaries.extractor import (
    BoundariesExtractor,
)
from threedi_modelchecker.simulation_templates.models import SimulationTemplate, Events
from threedi_modelchecker.simulation_templates.settings.extractor import (
    SettingsExtractor,
)
from threedi_modelchecker.simulation_templates.structure_controls.extractor import (
    StructureControlExtractor,
)
from threedi_modelchecker.threedi_database import ThreediDatabase
from threedi_modelchecker.threedi_model.models import GlobalSetting
from sqlalchemy.orm import Query


class SimulationTemplateExtractor(object):
    def __init__(self, sqlite_path: Path, global_settings_id: Optional[int] = None):
        """
        param global_settings_id: if None the first global setting entry is taken (default)
        """
        self.sqlite_path = sqlite_path
        self.global_settings_id = global_settings_id
        self.database = ThreediDatabase(
            connection_settings={"db_path": self.sqlite_path.as_posix()},
            db_type="spatialite",
        )

    def _extract_simulation_template(self, session: Session) -> SimulationTemplate:
        """
        Extract a SimulationTemplate instance using the given database session
        """
        qr = Query(GlobalSetting).with_session(session)
        if self.global_settings_id is not None:
            qr = qr.filter(GlobalSetting.id == self.global_settings_id)
        global_settings: GlobalSetting = qr.first()

        initial_waterlevels = InitialWaterlevelExtractor(
            session, self.global_settings_id
        )

        settings = SettingsExtractor(session, global_settings.id)

        return SimulationTemplate(
            events=Events(
                structure_controls=StructureControlExtractor(
                    session, control_group_id=global_settings.control_group_id
                ).all_controls(),
                laterals=LateralsExtractor(session).as_list(),
                boundaries=BoundariesExtractor(session).as_list(),
            ),
            settings=settings.all_settings(),
            initial_waterlevels=initial_waterlevels.all_initial_waterlevels(),
        )

    def extract(self) -> SimulationTemplate:
        """
        Return simulation template for
        """
        try:
            session = self.database.get_session()
            return self._extract_simulation_template(session)
        finally:
            session.close()
