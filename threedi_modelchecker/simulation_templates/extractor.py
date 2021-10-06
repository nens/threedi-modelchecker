from pathlib import Path
from typing import List, Dict, Optional
from threedi_modelchecker.simulation_templates.initial_waterlevels.extractor import InitialWaterlevelExtractor
from threedi_modelchecker.simulation_templates.laterals.extractor import LateralsExtractor
from threedi_modelchecker.simulation_templates.boundaries.extractor import BoundariesExtractor
from threedi_modelchecker.simulation_templates.models import SimulationTemplate, Events
from threedi_modelchecker.simulation_templates.settings.extractor import SettingsExtractor
from threedi_modelchecker.simulation_templates.structure_controls.extractor import StructureControlExtractor
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
            connection_settings={
                "db_path": self.sqlite_path.as_posix()},
                db_type="spatialite"
        )

    @property
    def instance(self) -> SimulationTemplate:
        """
        Return simulation template as one dict
        """
        try:
            session = self.database.get_session()
        
            qr = Query(GlobalSetting).with_session(session)
            if self.global_settings_id is not None:
                qr = qr.filter(GlobalSetting.id==self.global_settings_id)
            global_settings: GlobalSetting = qr.first()

            initial_waterlevels = InitialWaterlevelExtractor(session, self.global_settings_id)

            settings = SettingsExtractor(session, global_settings.id)

            return SimulationTemplate(
                events=Events(
                    structure_controls=StructureControlExtractor(
                        session, control_group_id=global_settings.control_group_id).all_controls(),
                    laterals=LateralsExtractor(session).as_list(),
                    boundaries=BoundariesExtractor(session).as_list(),
                ),
                settings=settings.all_settings(),
                initial_waterlevels=initial_waterlevels.all_initial_waterlevels()
            )
        finally:
            session.close()


def main():
    from threedi_api_client.api import ThreediApi
    from threedi_api_client.versions import V3BetaApi
    from threedi_api_client.openapi.models import Simulation
    sqlite_fi1le = "/srv/nens/models/t0224_velsen_velsen_noord/92e041d46a810d97fd6120ffa5ba0b81935f5d0d/velsen_noord_1d_reeks.sqlite" 

    sqlite_file = "/srv/nens/models/testbank_3di/137_2D_FlowObstacleWall_lateral/137_2D_FlowObstacleWall_lateral.sqlite"
    sqlite_file = "/srv/nens/models/testbank_3di/206_2D_interflw_lateral/206_2D_interflw_lateral.sqlite"
    sqlite_file = "/srv/nens/models/u0238_papendrecht/2602caf5138245e3d4f59f547e5911547a3cb54f/papendrecht_integraal.sqlite"

    sqlite_file = "/srv/nens/models/t0224_velsen_velsen_noord/92e041d46a810d97fd6120ffa5ba0b81935f5d0d/velsen_noord_1d2d.sqlite"

    #sqlite_file = "/srv/nens/models/testbank_3di/2005_hor_inf_full/2005_hor_inf_full.sqlite"

    # sqlite_file = "/srv/nens/models/testbank_3di/2007_hor_inf_spat_var_sat/2007_hor_inf_spat_var_sat.sqlite"


    


    #sqlite_file = "/srv/nens/models/hoorn2d/6c8365652f8eb04d33004f323eeac5a0f481a159/hoornpuur2d.sqlite"
    #threedimodel_id = 24
    

    #sqlite_file = "/srv/nens/models/v2_bergermeer/3a58dfb2e95f10ca121e26e4259ed68f60e3268f/v2_bergermeer.sqlite"
    #threedimodel_id = 1

    sqlite_file = "/srv/nens/models/texel-off-grid/8578f8f0dc458719a0bb6aae9c908ca2cbe385da/texel_offgrid.sqlite"
    threedimodel_id = 2

    x  = SimulationTemplateExtractor(Path(sqlite_file))
    yy = x.instance
    dd = yy.as_dict()

    d1 = SimulationTemplate.from_dict(dd)

    create = False

    if not create: 
        import ipdb; ipdb.set_trace()

    if create:
        # Try to upload
        client: V3BetaApi = ThreediApi(
            config={
                "THREEDI_API_USERNAME": "root",
                "THREEDI_API_PASSWORD": "root2",
                "THREEDI_API_HOST": "http://localhost:8000"}
        )
        sim = Simulation(
            name="test_sim", 
            threedimodel=threedimodel_id, 
            organisation="b08433fa47c1401eb9cbd4156034c679",
            start_datetime="2021-10-06T09:32:38.222", duration=3600)
        sim: Simulation = client.simulations_create(sim)

        # Try to save to API!!!
        yy.save_to_api(client, sim)

        print("DONE", sim.id)

        import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    main()