from sqlalchemy.orm import Query
from sqlalchemy import func, distinct

from model_checker import models
from model_checker.models import Manhole, ConnectionNode


def check_foreign_key(session, origin_column, ref_column):
    """Check all values in origin_column are in ref_column.

    Null values are ignored.

    :param session: sqlalchemy.orm.session.Session
    :param origin_column: InstrumentedAttribute
    :param ref_column: InstrumentedAttribute
    :return: list of declared models instances of origin_column.class
    """
    # q = session.query(origin_column.class_).filter(origin_column.notin_(
    #     session.query(ref_column)
    # ))
    q = session.query(origin_column.class_).filter(
        origin_column.notin_(session.query(ref_column)),
        origin_column != None
    )
    return q.all()


def check_unique(session, column):
    """Return all values in column that are not unique

    Null values are ignored.

    :param session:
    :param column: InstrumentedAttribute
    :return: list of declared models instances of column.class
    """
    distinct_count = session.query(func.count(distinct(column))).scalar()
    all_count = session.query(func.count(column)).scalar()
    if distinct_count == all_count:
        return []
    duplicate_values = session.query(column).group_by(column).having(
        func.count(column) > 1)
    # get the complete objects
    q = session.query(column.class_).filter(column.in_(duplicate_values))
    return q.all()


def check_not_null(session, column):
    """Return all values that are not null

    :param self:
    :param session:
    :param column:
    :return:
    """
    q = session.query(column.class_).filter(column == None)
    return q.all()


def check_valid_geom():
    pass


def check_timeseries_format():
    pass


# Constraints only added to the postgis (work) db in
# threedi-tools.sql.database_connections
# many more...
def has_two_connection_nodes(table_name):
    pass


def must_be_on_channel(windshielding_table_name):
    pass


class ThreediModelChecker:

    def __init__(self, threedi_db):
        self.db = threedi_db

    def check_foreign_keys(self):
        results = []
        session = self.db.get_session()

        foreign_keys_to_check = [
            (models.BoundaryCondition1D.connection_node_id, models.ConnectionNode.id),
            (models.Lateral1d.connection_node_id, models.ConnectionNode.id),
            (models.AggregationSettings.global_settings_id, models.GlobalSetting.id),
            (models.Channel.connection_node_start_id, models.ConnectionNode.id),
            (models.Channel.connection_node_end_id, models.ConnectionNode.id),
            (models.ConnectedPoint.calculation_pnt_id, models.CalculationPoint.id),
            (models.ConnectedPoint.levee_id, models.Levee.id),
            (models.Control.control_group_id, models.ControlGroup.id),
            (models.Control.measure_group_id, models.ControlMeasureGroup.id),
            (models.ControlMeasureMap.measure_group_id, models.ControlMeasureGroup.id),
            (models.CrossSectionLocation.definition_id, models.CrossSectionDefinition.id),
            (models.CrossSectionLocation.channel_id, models.Channel.id),
            (models.Culvert.connection_node_start_id, models.ConnectionNode.id),
            (models.Culvert.connection_node_end_id, models.ConnectionNode.id),
            (models.Culvert.cross_section_definition_id, models.CrossSectionDefinition.id),
            (models.GlobalSetting.numerical_settings_id, models.NumericalSettings.id),
            (models.GlobalSetting.interflow_settings_id, models.Interflow.id),
            (models.GlobalSetting.control_group_id, models.ControlGroup.id),
            (models.GlobalSetting.simple_infiltration_settings_id, models.SimpleInfiltration.id),
            (models.GlobalSetting.groundwater_settings_id, models.GroundWater.id),
            (models.ImperviousSurfaceMap.impervious_surface_id, models.ImperviousSurface.id),
            (models.ImperviousSurfaceMap.connection_node_id, models.ConnectionNode.id),
            (models.Manhole.connection_node_id, models.ConnectionNode.id),
            (models.Orifice.connection_node_end_id, models.ConnectionNode.id),
            (models.Orifice.connection_node_start_id, models.ConnectionNode.id),
            (models.Orifice.cross_section_definition_id, models.CrossSectionDefinition.id),
            (models.Pipe.connection_node_start_id, models.ConnectionNode.id),
            (models.Pipe.connection_node_end_id, models.ConnectionNode.id),
            (models.Pipe.cross_section_definition_id, models.CrossSectionDefinition.id),
            (models.Pumpstation.connection_node_start_id, models.ConnectionNode.id),
            (models.Pumpstation.connection_node_end_id, models.ConnectionNode.id),
            (models.Surface.surface_parameters_id, models.SurfaceParameter.id),
            (models.SurfaceMap.connection_node_id, models.ConnectionNode.id),
            (models.Weir.connection_node_start_id, models.ConnectionNode.id),
            (models.Weir.connection_node_end_id, models.ConnectionNode.id),
            (models.Weir.cross_section_definition_id, models.CrossSectionDefinition.id),
            (models.Windshielding.channel_id, models.Channel.id)
        ]

        for origin_column, ref_column in foreign_keys_to_check:
            missing_fk = check_foreign_key(session, origin_column, ref_column)
            if len(missing_fk) > 0:
                print("ohoh!")
            results += missing_fk

        return results

class ModelCheckResult:

    status_code = None
    # Resolved/Unresolved

    severity = None
    # Error/Warning

    def __init__(self):
        pass
