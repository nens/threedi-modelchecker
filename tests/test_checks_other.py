from . import factories
from .factories import BoundaryConditions2DFactory
from geoalchemy2 import functions as geo_func
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Query
from threedi_modelchecker.checks.other import BankLevelCheck
from threedi_modelchecker.checks.other import ConnectionNodesDistance
from threedi_modelchecker.checks.other import ConnectionNodesLength
from threedi_modelchecker.checks.other import OpenChannelsWithNestedNewton
from threedi_modelchecker.checks.other import TimeseriesCheck
from threedi_modelchecker.threedi_model import constants
from threedi_modelchecker.threedi_model import models

import pytest


def test_check_cross_section_location_bank_levels(session):
    """Check 'CrossSectionLocation.bank_level' is not null if
    calculation_type is CONNECTED or DOUBLE_CONNECTED.
    """
    if session.bind.name == "postgresql":
        pytest.skip(
            "Postgis db has set constraints which make the "
            "channelfactory fail. Furthermore, it expects an SRID "
            "28992 while spatialite expects 4326."
        )
    channel = factories.ChannelFactory(
        calculation_type=constants.CalculationType.CONNECTED
    )
    wrong = factories.CrossSectionLocationFactory(channel=channel, bank_level=None)
    factories.CrossSectionLocationFactory(channel=channel, bank_level=1.0)
    factories.CrossSectionLocationFactory(
        channel=factories.ChannelFactory(
            calculation_type=constants.CalculationType.EMBEDDED
        ),
        bank_level=None,
    )

    bank_level_check = BankLevelCheck()
    invalid_bank_levels = bank_level_check.get_invalid(session)
    assert len(invalid_bank_levels) == 1
    assert invalid_bank_levels[0].id == wrong.id


@pytest.mark.parametrize("timeseries", ["0,-0.5", "0,-0.5 \n59, -0.5\n60 ,-0.5\n   "])
def test_timeseries_check(session, timeseries):
    BoundaryConditions2DFactory()

    check = TimeseriesCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


def test_timeseries_check_multiple(session):
    BoundaryConditions2DFactory.create_batch(3)

    check = TimeseriesCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


def test_timeseries_check_different_timesteps(session):
    BoundaryConditions2DFactory(timeseries="0,-0.5\n1,1.4\n2,4.0")
    boundary_condition2 = BoundaryConditions2DFactory(
        timeseries="0,-0.5\n1,1.4\n3,4.0"  # Note the last timestep is 3 instead of 2
    )

    check = TimeseriesCheck(models.BoundaryConditions2D.timeseries)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1
    assert invalid[0].id == boundary_condition2.id


def test_connection_nodes_length(session):
    if session.bind.name == "postgresql":
        pytest.skip("Postgres only accepts coords in epsg 4326")
    factories.GlobalSettingsFactory(epsg_code=28992)
    factories.WeirFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222995634060702 -0.13872239147499893)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.3822292515698168 -0.1387223869163263)"
        ),
    )
    weir_too_short = factories.WeirFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222938832999598 -0.13872236685816669)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222930900909202 -0.13872236685816669)"
        ),
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 1
    assert errors[0].id == weir_too_short.id


def test_connection_nodes_length_missing_epsg_code(session):
    if session.bind.name == "postgresql":
        pytest.skip("Postgres only accepts coords in epsg 4326")
    factories.WeirFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222938832999598 -0.13872236685816669)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222930900909202 -0.13872236685816669)"
        ),
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 0


def test_connection_nodes_length_missing_start_node(session):
    if session.bind.name == "postgresql":
        pytest.skip("Postgres only accepts coords in epsg 4326")
    factories.GlobalSettingsFactory(epsg_code=28992)
    factories.WeirFactory(
        connection_node_start=None,
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222930900909202 -0.13872236685816669)"
        ),
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 0


def test_connection_nodes_length_missing_end_node(session):
    if session.bind.name == "postgresql":
        pytest.skip("Postgres only accepts coords in epsg 4326")
    factories.GlobalSettingsFactory(epsg_code=28992)
    factories.WeirFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222930900909202 -0.13872236685816669)"
        ),
        connection_node_end=None,
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 0


def test_open_channels_with_nested_newton(session):
    factories.NumericalSettingsFactory(use_of_nested_newton=0)
    channel = factories.ChannelFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-71.064544 42.28787)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-71.0645 42.287)"
        ),
        the_geom="SRID=4326;LINESTRING(-71.064544 42.28787, -71.0645 42.287)",
    )
    open_definition = factories.CrossSectionDefinitionFactory(
        shape=constants.CrossSectionShape.TABULATED_TRAPEZIUM, width="1 0"
    )
    factories.CrossSectionLocationFactory(
        channel=channel,
        definition=open_definition,
        the_geom="SRID=4326;POINT(-71.0645 42.287)",
    )

    channel2 = factories.ChannelFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-71.064544 42.28787)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-71.0645 42.287)"
        ),
        the_geom="SRID=4326;LINESTRING(-71.064544 42.28787, -71.0645 42.287)",
    )
    open_definition_egg = factories.CrossSectionDefinitionFactory(
        shape=constants.CrossSectionShape.EGG,
    )
    factories.CrossSectionLocationFactory(
        channel=channel2,
        definition=open_definition_egg,
        the_geom="SRID=4326;POINT(-71.0645 42.287)",
    )

    check = OpenChannelsWithNestedNewton()

    errors = check.get_invalid(session)
    assert len(errors) == 2


def test_node_distance(session):
    if session.bind.name == "postgresql":
        pytest.skip("Check only applicable to spatialite")
    con1_too_close = factories.ConnectionNodeFactory(
        the_geom="SRID=4326;POINT(4.728282 52.64579283592512)"
    )
    con2_too_close = factories.ConnectionNodeFactory(
        the_geom="SRID=4326;POINT(4.72828 52.64579283592512)"
    )
    # Good distance
    factories.ConnectionNodeFactory(
        the_geom="SRID=4326;POINT(4.726838755789598 52.64514133594995)"
    )

    # sanity check to see the distances between the nodes
    node_a = aliased(models.ConnectionNode)
    node_b = aliased(models.ConnectionNode)
    distances_query = Query(
        geo_func.ST_Distance(node_a.the_geom, node_b.the_geom, 1)
    ).filter(node_a.id != node_b.id)
    # Shows the distances between all 3 nodes: node 1 and 2 are too close
    distances_query.with_session(session).all()

    check = ConnectionNodesDistance(minimum_distance=10)
    invalid = check.get_invalid(session)
    assert len(invalid) == 2
    invalid_ids = [i.id for i in invalid]
    assert con1_too_close.id in invalid_ids
    assert con2_too_close.id in invalid_ids
