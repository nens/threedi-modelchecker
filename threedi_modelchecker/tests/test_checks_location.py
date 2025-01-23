import pytest
from threedi_schema.domain import models

from threedi_modelchecker.checks.location import (
    ConnectionNodeLinestringLocationCheck,
    DWFMapLinestringLocationCheck,
    LinestringLocationCheck,
    MeasureMapLinestringMapLocationCheck,
    PointLocationCheck,
    PumpMapLinestringLocationCheck,
    SurfaceMapLinestringLocationCheck,
)
from threedi_modelchecker.tests import factories

SRID = 28992
POINT1 = "142742 473443"
POINT2 = "142743 473443"  # POINT1 + 1 meter
POINT3 = "142747 473443"  # POINT1 + 5 meter


@pytest.mark.parametrize(
    "bc_geom, nof_invalid", [(POINT1, 0), (POINT2, 0), (POINT3, 1)]
)
def test_point_location_check(session, bc_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=0, geom=f"SRID={SRID};POINT({POINT1})")
    factories.BoundaryConditions1DFactory(
        id=0, connection_node_id=0, geom=f"SRID={SRID};POINT({bc_geom})"
    )
    errors = PointLocationCheck(
        column=models.BoundaryCondition1D.geom,
        ref_column=models.BoundaryCondition1D.connection_node_id,
        ref_table=models.ConnectionNode,
        max_distance=1,
    ).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        (f"LINESTRING({POINT1}, {POINT3})", 0),
        (f"LINESTRING({POINT2}, {POINT3})", 0),  # within tolerance
        (f"LINESTRING({POINT3}, {POINT1})", 0),  # reversed
        (f"LINESTRING({POINT3}, {POINT2})", 0),  # within tolerance, within tolerance
        (f"LINESTRING(142732 473443, {POINT3})", 1),  # startpoint is wrong
        (f"LINESTRING({POINT1}, 142752 473443)", 1),  # endpoint is wrong
    ],
)
def test_linestring_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.ConnectionNodeFactory(id=2, geom=f"SRID={SRID};POINT({POINT3})")
    factories.ChannelFactory(
        connection_node_id_start=1,
        connection_node_id_end=2,
        geom=f"SRID={SRID};{channel_geom}",
    )
    errors = LinestringLocationCheck(
        column=models.Channel.geom,
        ref_column_start=models.Channel.connection_node_id_start,
        ref_column_end=models.Channel.connection_node_id_end,
        ref_table_start=models.ConnectionNode,
        ref_table_end=models.ConnectionNode,
        max_distance=1.01,
    ).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        (f"LINESTRING({POINT1}, {POINT3})", 0),
        (f"LINESTRING(142732 473443, {POINT3})", 1),  # startpoint is wrong
    ],
)
def test_connection_node_linestring_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.ConnectionNodeFactory(id=2, geom=f"SRID={SRID};POINT({POINT3})")
    factories.ChannelFactory(
        connection_node_id_start=1,
        connection_node_id_end=2,
        geom=f"SRID={SRID};{channel_geom}",
    )
    errors = ConnectionNodeLinestringLocationCheck(
        column=models.Channel.geom, max_distance=1.01
    ).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        (f"LINESTRING({POINT1}, {POINT3})", 0),
        (f"LINESTRING(142732 473443, {POINT3})", 1),  # startpoint is wrong
    ],
)
@pytest.mark.parametrize(
    "control_table, control_type",
    [(models.MemoryControl, "memory"), (models.TableControl, "table")],
)
def test_control_measure_map_linestring_map_location_check(
    session, control_table, control_type, channel_geom, nof_invalid
):
    factories.MeasureLocationFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.MemoryControlFactory(id=1, geom=f"SRID={SRID};POINT({POINT3})")
    factories.TableControlFactory(id=1, geom=f"SRID={SRID};POINT({POINT3})")
    factories.MeasureMapFactory(
        measure_location_id=1,
        control_id=1,
        control_type="memory",
        geom=f"SRID={SRID};{channel_geom}",
    )
    factories.MeasureMapFactory(
        measure_location_id=1,
        control_id=1,
        control_type="table",
        geom=f"SRID={SRID};{channel_geom}",
    )
    errors = MeasureMapLinestringMapLocationCheck(
        control_table=control_table,
        filters=models.MeasureMap.control_type == control_type,
        max_distance=1.01,
    ).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        (f"LINESTRING({POINT1}, {POINT3})", 0),
        (f"LINESTRING(142732 473443, {POINT3})", 1),  # startpoint is wrong
    ],
)
def test_dwf_map_linestring_map_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")

    factories.DryWeatherFlowFactory(
        id=1,
        geom=f"SRID={SRID};POLYGON(({POINT1}, {POINT3}, 142742 473445, {POINT1}))",
    )
    factories.DryWheatherFlowMapFactory(
        connection_node_id=1, dry_weather_flow_id=1, geom=f"SRID={SRID};{channel_geom}"
    )
    errors = DWFMapLinestringLocationCheck(max_distance=1.01).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        (f"LINESTRING({POINT1}, {POINT3})", 0),
        (f"LINESTRING(142732 473443, {POINT3})", 1),  # startpoint is wrong
    ],
)
def test_pump_map_linestring_map_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.PumpFactory(id=1, geom=f"SRID={SRID};POINT({POINT3})")
    factories.PumpMapFactory(
        connection_node_id_end=1, pump_id=1, geom=f"SRID={SRID};{channel_geom}"
    )
    errors = PumpMapLinestringLocationCheck(max_distance=1.01).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        (f"LINESTRING({POINT1}, {POINT3})", 0),
        (f"LINESTRING(142732 473443, {POINT3})", 1),  # startpoint is wrong
    ],
)
def test_surface_map_linestring_map_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.SurfaceFactory(
        id=1,
        geom=f"SRID={SRID};POLYGON(({POINT1}, {POINT3}, 142742 473445, {POINT1}))",
    )
    factories.SurfaceMapFactory(
        connection_node_id=1, surface_id=1, geom=f"SRID={SRID};{channel_geom}"
    )
    errors = SurfaceMapLinestringLocationCheck(max_distance=1.01).get_invalid(session)
    assert len(errors) == nof_invalid
