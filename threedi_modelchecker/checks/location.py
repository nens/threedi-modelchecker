from typing import List, NamedTuple

from geoalchemy2.functions import ST_Distance, ST_NPoints, ST_PointN
from sqlalchemy.orm import aliased, Session
from threedi_schema.domain import models

from threedi_modelchecker.checks.base import BaseCheck


class PointLocationCheck(BaseCheck):
    """Check if cross section locations are within {max_distance} of their channel."""

    def __init__(
        self,
        ref_column,
        ref_table,
        max_distance,
        *args,
        **kwargs,
    ):
        self.max_distance = max_distance
        self.ref_column = ref_column
        self.ref_table = ref_table
        super().__init__(*args, **kwargs)

    def get_invalid(self, session):
        # get all channels with more than 1 cross section location
        return (
            self.to_check(session)
            .join(
                self.ref_table,
                self.ref_table.id == self.ref_column,
            )
            .filter(ST_Distance(self.column, self.ref_table.geom) > self.max_distance)
            .all()
        )

    def description(self):
        return (
            f"{self.column_name} does not match the position of the object that "
            f"{self.table.name}.{self.ref_column} refers to"
        )


class LinestringLocationCheck(BaseCheck):
    """Check that linestring geometry starts / ends are close to their connection nodes

    This allows for reversing the geometries. threedi-gridbuilder will reverse the geometries if
    that lowers the distance to the connection nodes.
    """

    def __init__(
        self,
        ref_column_start,
        ref_column_end,
        ref_table_start,
        ref_table_end,
        max_distance,
        *args,
        **kwargs,
    ):
        self.max_distance = max_distance
        self.ref_column_start = ref_column_start
        self.ref_column_end = ref_column_end
        self.ref_table_start = ref_table_start
        self.ref_table_end = ref_table_end
        super().__init__(*args, **kwargs)

    def get_invalid(self, session: Session) -> List[NamedTuple]:
        start_node = aliased(self.ref_table_start)
        end_node = aliased(self.ref_table_end)
        tol = self.max_distance
        start_point = ST_PointN(self.column, 1)
        end_point = ST_PointN(self.column, ST_NPoints(self.column))
        start_ok = ST_Distance(start_point, start_node.geom) <= tol
        end_ok = ST_Distance(end_point, end_node.geom) <= tol
        start_ok_if_reversed = ST_Distance(end_point, start_node.geom) <= tol
        end_ok_if_reversed = ST_Distance(start_point, end_node.geom) <= tol
        return (
            self.to_check(session)
            .join(start_node, start_node.id == self.ref_column_start)
            .join(end_node, end_node.id == self.ref_column_end)
            .filter(
                ~(start_ok & end_ok),
                ~(start_ok_if_reversed & end_ok_if_reversed),
            )
            .all()
        )

    def description(self) -> str:
        ref_start_name = f"{self.table.name}.{self.ref_column_start.name}"
        ref_end_name = f"{self.table.name}.{self.ref_column_end.name}"
        return f"{self.column_name} does not start or end at its connection nodes: {ref_start_name} and {ref_end_name} (tolerance = {self.max_distance} m)"


class ConnectionNodeLinestringLocationCheck(LinestringLocationCheck):
    def __init__(self, column, *args, **kwargs):
        table = column.table
        super().__init__(
            ref_column_start=table.c.connection_node_id_start,
            ref_column_end=table.c.connection_node_id_end,
            ref_table_start=models.ConnectionNode,
            ref_table_end=models.ConnectionNode,
            column=column,
            *args,
            **kwargs,
        )

    def description(self) -> str:
        return f"{self.column_name} does not start or end at its connection node (tolerance = {self.max_distance} m)"


class MeasureMapLinestringMapLocationCheck(LinestringLocationCheck):
    def __init__(self, control_table, filters, *args, **kwargs):
        super().__init__(
            ref_column_start=models.MeasureMap.measure_location_id,
            ref_column_end=models.MeasureMap.control_id,
            ref_table_start=models.MeasureLocation,
            ref_table_end=control_table,
            column=models.MeasureMap.geom,
            filters=filters,
            *args,
            **kwargs,
        )


class DWFMapLinestringLocationCheck(LinestringLocationCheck):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ref_column_start=models.DryWeatherFlowMap.connection_node_id,
            ref_column_end=models.DryWeatherFlowMap.dry_weather_flow_id,
            ref_table_start=models.ConnectionNode,
            ref_table_end=models.DryWeatherFlow,
            column=models.DryWeatherFlowMap.geom,
            *args,
            **kwargs,
        )


class PumpMapLinestringLocationCheck(LinestringLocationCheck):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ref_column_start=models.PumpMap.pump_id,
            ref_column_end=models.PumpMap.connection_node_id_end,
            ref_table_start=models.Pump,
            ref_table_end=models.ConnectionNode,
            column=models.PumpMap.geom,
            *args,
            **kwargs,
        )


class SurfaceMapLinestringLocationCheck(LinestringLocationCheck):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ref_column_start=models.SurfaceMap.surface_id,
            ref_column_end=models.SurfaceMap.connection_node_id,
            ref_table_start=models.Surface,
            ref_table_end=models.ConnectionNode,
            column=models.SurfaceMap.geom,
            *args,
            **kwargs,
        )
