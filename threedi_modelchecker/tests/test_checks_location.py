import pytest
from threedi_schema.domain import models

from threedi_modelchecker.checks.location import (
    ConnectionNodeLinestringLocationCheck,
    ControlMeasureMapLinestringMapLocationCheck,
    DWFMapLinestringLocationCheck,
    LinestringLocationCheck,
    PointLocationCheck,
    PumpMapLinestringLocationCheck,
    SurfaceMapLinestringLocationCheck,
)
from threedi_modelchecker.tests import factories


def test_point_location_check(session):
    factories.ChannelFactory(
        id=1,
        geom="SRID=4326;LINESTRING(5.387204 52.155172, 5.387204 52.155262)",
    )
    factories.CrossSectionLocationFactory(
        channel_id=1, geom="SRID=4326;POINT(5.387204 52.155200)"
    )
    factories.CrossSectionLocationFactory(
        channel_id=1, geom="SRID=4326;POINT(5.387218 52.155244)"
    )
    errors = PointLocationCheck(
        column=models.CrossSectionLocation.geom,
        ref_column=models.CrossSectionLocation.channel_id,
        ref_table=models.Channel,
        max_distance=0.1,
    ).get_invalid(session)
    assert len(errors) == 1


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        ("LINESTRING(5.387204 52.155172, 5.387204 52.155262)", 0),
        ("LINESTRING(5.387218 52.155172, 5.387218 52.155262)", 0),  # within tolerance
        ("LINESTRING(5.387204 52.155262, 5.387204 52.155172)", 0),  # reversed
        (
            "LINESTRING(5.387218 52.155262, 5.387218 52.155172)",
            0,
        ),  # reversed, within tolerance
        (
            "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",
            1,
        ),  # startpoint is wrong
        ("LINESTRING(5.387204 52.155172, 5.387204 52.164151)", 1),  # endpoint is wrong
    ],
)
def test_linestring_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155172)")
    factories.ConnectionNodeFactory(id=2, geom="SRID=4326;POINT(5.387204 52.155262)")
    factories.ChannelFactory(
        connection_node_id_start=1,
        connection_node_id_end=2,
        geom=f"SRID=4326;{channel_geom}",
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
        ("LINESTRING(5.387204 52.155172, 5.387204 52.155262)", 0),
        (
            "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",
            1,
        ),  # startpoint is wrong
    ],
)
def test_connection_node_linestring_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155172)")
    factories.ConnectionNodeFactory(id=2, geom="SRID=4326;POINT(5.387204 52.155262)")
    factories.ChannelFactory(
        connection_node_id_start=1,
        connection_node_id_end=2,
        geom=f"SRID=4326;{channel_geom}",
    )
    errors = ConnectionNodeLinestringLocationCheck(
        column=models.Channel.geom, max_distance=1.01
    ).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        ("LINESTRING(5.387204 52.155172, 5.387204 52.155262)", 0),
        (
            "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",
            1,
        ),  # startpoint is wrong
    ],
)
@pytest.mark.parametrize(
    "control_table, control_type",
    [(models.ControlMemory, "memory"), (models.ControlTable, "table")],
)
def test_control_measure_map_linestring_map_location_check(
    session, control_table, control_type, channel_geom, nof_invalid
):
    factories.ControlMeasureLocationFactory(
        id=1, geom="SRID=4326;POINT(5.387204 52.155172)"
    )
    factories.ControlMemoryFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155262)")
    factories.ControlTableFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155262)")
    factories.ControlMeasureMapFactory(
        measure_location_id=1,
        control_id=1,
        control_type="memory",
        geom=f"SRID=4326;{channel_geom}",
    )
    factories.ControlMeasureMapFactory(
        measure_location_id=1,
        control_id=1,
        control_type="table",
        geom=f"SRID=4326;{channel_geom}",
    )
    errors = ControlMeasureMapLinestringMapLocationCheck(
        control_table=control_table,
        filters=models.ControlMeasureMap.control_type == control_type,
        max_distance=1.01,
    ).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        ("LINESTRING(5.387204 52.155172, 5.387204 52.155262)", 0),
        (
            "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",
            1,
        ),  # startpoint is wrong
    ],
)
def test_dwf_map_linestring_map_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155172)")
    factories.DryWeatherFlowFactory(
        id=1,
        geom="SRID=4326;POLYGON((5.387204 52.155262, 5.387204 52.155172, 5.387304 52.155172, 5.387304 52.155262, 5.387204 52.155262))",
    )
    factories.DryWheatherFlowMapFactory(
        connection_node_id=1,
        dry_weather_flow_id=1,
        geom=f"SRID=4326;{channel_geom}",
    )
    errors = DWFMapLinestringLocationCheck(max_distance=1.01).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        ("LINESTRING(5.387204 52.155172, 5.387204 52.155262)", 0),
        (
            "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",
            1,
        ),  # startpoint is wrong
    ],
)
def test_pump_map_linestring_map_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155172)")
    factories.PumpFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155262)")
    factories.PumpMapFactory(
        connection_node_id_end=1,
        pump_id=1,
        geom=f"SRID=4326;{channel_geom}",
    )
    errors = PumpMapLinestringLocationCheck(max_distance=1.01).get_invalid(session)
    assert len(errors) == nof_invalid


@pytest.mark.parametrize(
    "channel_geom, nof_invalid",
    [
        ("LINESTRING(5.387204 52.155172, 5.387204 52.155262)", 0),
        (
            "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",
            1,
        ),  # startpoint is wrong
    ],
)
def test_surface_map_linestring_map_location_check(session, channel_geom, nof_invalid):
    factories.ConnectionNodeFactory(id=1, geom="SRID=4326;POINT(5.387204 52.155172)")
    factories.SurfaceFactory(
        id=1,
        geom="SRID=4326;POLYGON((5.387204 52.155262, 5.387204 52.155172, 5.387304 52.155172, 5.387304 52.155262, 5.387204 52.155262))",
    )
    factories.SurfaceMapFactory(
        connection_node_id=1,
        surface_id=1,
        geom=f"SRID=4326;{channel_geom}",
    )
    errors = SurfaceMapLinestringLocationCheck(max_distance=1.01).get_invalid(session)
    assert len(errors) == nof_invalid
