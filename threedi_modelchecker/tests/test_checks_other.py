from unittest import mock

import pytest
from sqlalchemy import func, text
from sqlalchemy.orm import aliased, Query
from threedi_schema import constants, models, ThreediDatabase
from threedi_schema.beta_features import BETA_COLUMNS, BETA_VALUES

from threedi_modelchecker.checks.other import (
    AllPresentFixedVegetationParameters,
    AllPresentVariableVegetationParameters,
    BetaColumnsCheck,
    BetaValuesCheck,
    ChannelManholeLevelCheck,
    ConnectionNodesDistance,
    ConnectionNodesLength,
    CorrectAggregationSettingsExist,
    CrossSectionLocationCheck,
    CrossSectionSameConfigurationCheck,
    DefinedAreaCheck,
    FeatureClosedCrossSectionCheck,
    ImperviousNodeInflowAreaCheck,
    InflowNoFeaturesCheck,
    LinestringLocationCheck,
    NodeSurfaceConnectionsCheck,
    OpenChannelsWithNestedNewton,
    PerviousNodeInflowAreaCheck,
    PotentialBreachInterdistanceCheck,
    PotentialBreachStartEndCheck,
    PumpStorageTimestepCheck,
    SpatialIndexCheck,
)
from threedi_modelchecker.model_checks import ThreediModelChecker

from . import factories


@pytest.mark.parametrize(
    "aggregation_method,flow_variable,expected_result",
    [
        (
            constants.AggregationMethod.CUMULATIVE,
            constants.FlowVariable.PUMP_DISCHARGE,
            0,
        ),  # entries in aggregation settings, valid
        (
            constants.AggregationMethod.CUMULATIVE,
            constants.FlowVariable.DISCHARGE,
            1,
        ),  # entries not in aggregation settings, invalid
    ],
)
def test_aggregation_settings(
    session, aggregation_method, flow_variable, expected_result
):
    factories.GlobalSettingsFactory(id=1)
    factories.AggregationSettingsFactory(
        global_settings_id=1,
        aggregation_method=constants.AggregationMethod.CUMULATIVE,
        flow_variable=constants.FlowVariable.PUMP_DISCHARGE,
    )
    check = CorrectAggregationSettingsExist(
        aggregation_method=aggregation_method, flow_variable=flow_variable
    )
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


def test_connection_nodes_length(session):
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


def test_connection_nodes_length_missing_start_node(session):
    factories.GlobalSettingsFactory(epsg_code=28992)
    factories.WeirFactory(
        connection_node_start_id=9999,
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
        connection_node_end_id=9999,
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


channel_manhole_level_testdata = [
    ("start", -1, -3, -2, 0),
    ("start", -3, -1, -2, 1),
    ("end", -3, -1, -2, 0),
    ("end", -1, -3, -2, 1),
]


@pytest.mark.parametrize(
    "manhole_location,starting_reference_level,ending_reference_level,manhole_level,errors_number",
    channel_manhole_level_testdata,
)
def test_channel_manhole_level_check(
    session,
    manhole_location,
    starting_reference_level,
    ending_reference_level,
    manhole_level,
    errors_number,
):
    # using factories, create one minimal test case which passes, and one which fails
    # once that works, parametrise.
    # use nested factories for channel and connectionNode
    starting_coordinates = "4.718300 52.696686"
    ending_coordinates = "4.718255 52.696709"
    start_node = factories.ConnectionNodeFactory(
        the_geom=f"SRID=4326;POINT({starting_coordinates})"
    )
    end_node = factories.ConnectionNodeFactory(
        the_geom=f"SRID=4326;POINT({ending_coordinates})"
    )
    channel = factories.ChannelFactory(
        the_geom=f"SRID=4326;LINESTRING({starting_coordinates}, {ending_coordinates})",
        connection_node_start=start_node,
        connection_node_end=end_node,
    )
    # starting cross-section location
    factories.CrossSectionLocationFactory(
        the_geom="SRID=4326;POINT(4.718278 52.696697)",
        reference_level=starting_reference_level,
        channel=channel,
    )
    # ending cross-section location
    factories.CrossSectionLocationFactory(
        the_geom="SRID=4326;POINT(4.718264 52.696704)",
        reference_level=ending_reference_level,
        channel=channel,
    )
    # manhole
    factories.ManholeFactory(
        connection_node=end_node if manhole_location == "end" else start_node,
        bottom_level=manhole_level,
    )
    check = ChannelManholeLevelCheck(nodes_to_check=manhole_location)
    errors = check.get_invalid(session)
    assert len(errors) == errors_number


def test_node_distance(session):
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
        func.ST_Distance(node_a.the_geom, node_b.the_geom, 1)
    ).filter(node_a.id != node_b.id)
    # Shows the distances between all 3 nodes: node 1 and 2 are too close
    distances_query.with_session(session).all()

    check = ConnectionNodesDistance(minimum_distance=10)
    invalid = check.get_invalid(session)
    assert len(invalid) == 2
    invalid_ids = [i.id for i in invalid]
    assert con1_too_close.id in invalid_ids
    assert con2_too_close.id in invalid_ids


@pytest.mark.parametrize(
    "channel_geom",
    [
        "LINESTRING(5.387204 52.155172, 5.387204 52.155262)",
        "LINESTRING(5.387218 52.155172, 5.387218 52.155262)",  # within tolerance
        "LINESTRING(5.387204 52.155262, 5.387204 52.155172)",  # reversed
        "LINESTRING(5.387218 52.155262, 5.387218 52.155172)",  # reversed, within tolerance
    ],
)
def test_channels_location_check(session, channel_geom):
    factories.ChannelFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(5.387204 52.155172)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(5.387204 52.155262)"
        ),
        the_geom=f"SRID=4326;{channel_geom}",
    )

    errors = LinestringLocationCheck(
        column=models.Channel.the_geom, max_distance=1.01
    ).get_invalid(session)
    assert len(errors) == 0


@pytest.mark.parametrize(
    "channel_geom",
    [
        "LINESTRING(5.387204 52.164151, 5.387204 52.155262)",  # startpoint is wrong
        "LINESTRING(5.387204 52.155172, 5.387204 52.164151)",  # endpoint is wrong
    ],
)
def test_channels_location_check_invalid(session, channel_geom):
    factories.ChannelFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(5.387204 52.155172)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(5.387204 52.155262)"
        ),
        the_geom=f"SRID=4326;{channel_geom}",
    )

    errors = LinestringLocationCheck(
        column=models.Channel.the_geom, max_distance=1.01
    ).get_invalid(session)
    assert len(errors) == 1


def test_cross_section_location(session):
    channel = factories.ChannelFactory(
        the_geom="SRID=4326;LINESTRING(5.387204 52.155172, 5.387204 52.155262)",
    )
    factories.CrossSectionLocationFactory(
        channel=channel, the_geom="SRID=4326;POINT(5.387204 52.155200)"
    )
    factories.CrossSectionLocationFactory(
        channel=channel, the_geom="SRID=4326;POINT(5.387218 52.155244)"
    )
    errors = CrossSectionLocationCheck(0.1).get_invalid(session)
    assert len(errors) == 1


@pytest.mark.parametrize(
    "shape, width, height, same_channels, ok",
    [
        # --- closed cross-sections ---
        # shapes 0, 2, 3 and 8 are always closed
        (0, "3", "4", True, False),
        *[(i, "3", None, True, False) for i in [2, 3, 8]],
        # shapes 5 and 6 are closed if the width at the highest increment (last number in the width string) is 0
        *[
            (
                i,
                "0 4.142 5.143 5.143 5.869 0",
                "0 0.174 0.348 0.522 0.696 0.87",
                True,
                False,
            )
            for i in [5, 6]
        ],
        # shape 7 is closed if the first and last (width, height) coordinates are the same
        (7, "2 4.142 5.143 5.143 5.869 2", "3 0.174 0.348 0.522 0.696 3", True, False),
        #
        # --- open cross-sections ---
        # shape 1 is always open
        (1, "3", "4", True, True),
        # shapes 5 and 6 are open if the width at the highest increment (last number in the width string) is > 0
        *[
            (
                i,
                "0 4.142 5.143 5.143 5.869 1",
                "0 0.174 0.348 0.522 0.696 0.87",
                True,
                True,
            )
            for i in [5, 6]
        ],
        # shape 7 is open if the first and last (width, height) coordinates are not the same
        # different width
        (7, "2 4.142 5.143 5.143 5.869 3", "4 0.174 0.348 0.522 0.696 4", True, True),
        # different height
        (7, "2 4.142 5.143 5.143 5.869 2", "3 0.174 0.348 0.522 0.696 4", True, True),
        # different height and width
        (7, "2 4.142 5.143 5.143 5.869 3", "4 0.174 0.348 0.522 0.696 5", True, True),
        #
        # Bad data, should silently fail, returning no invalid rows. The data is checked in other checks.
        (7, "foo", "bar", True, True),
        #
        # Check on different channels
        # this should fail if the cross-sections are on the same channel, but pass on different channels
        (0, "3", "4", False, True),
    ],
)
def test_cross_section_same_configuration(
    session, shape, width, height, same_channels, ok
):
    """
    This test checks two cross-sections on a channel against each other; they should both be open or both be closed.
    In this test, the first cross-section has been set to always be open.
    Therefore, the channel should be invalid when the second cross-section is closed, and valid when it is open.
    """
    first_channel = factories.ChannelFactory(
        the_geom="SRID=4326;LINESTRING(4.718301 52.696686, 4.718255 52.696709)",
    )
    second_channel = factories.ChannelFactory(
        the_geom="SRID=4326;LINESTRING(4.718301 52.696686, 4.718255 52.696709)",
    )
    # shape 1 is always open
    open_definition = factories.CrossSectionDefinitionFactory(
        id=1, shape=1, width="3", height="4"
    )
    factories.CrossSectionLocationFactory(
        channel=first_channel,
        the_geom="SRID=4326;POINT(4.718278 52.696697)",
        definition=open_definition,
    )
    testing_definition = factories.CrossSectionDefinitionFactory(
        id=2, width=width, height=height, shape=shape
    )
    # the second one is parametrised
    factories.CrossSectionLocationFactory(
        channel=first_channel if same_channels else second_channel,
        the_geom="SRID=4326;POINT(4.718265 52.696704)",
        definition=testing_definition,
    )
    errors = CrossSectionSameConfigurationCheck(models.Channel.id).get_invalid(session)
    assert len(errors) == (0 if ok else 1)


def test_spatial_index_ok(session):
    check = SpatialIndexCheck(models.ConnectionNode.the_geom)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


def test_spatial_index_disabled(empty_sqlite_v4):
    session = empty_sqlite_v4.get_session()
    session.execute(
        text("SELECT DisableSpatialIndex('v2_connection_nodes', 'the_geom')")
    )
    check = SpatialIndexCheck(models.ConnectionNode.the_geom)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1


@pytest.mark.parametrize(
    "x,y,ok",
    [
        (-71.064544, 42.28787, True),  # at start
        (-71.0645, 42.287, True),  # at end
        (-71.06452, 42.2874, True),  # middle
        (-71.064544, 42.287869, False),  # close to start
        (-71.064499, 42.287001, False),  # close to end
    ],
)
def test_potential_breach_start_end(session, x, y, ok):
    # channel geom: LINESTRING (-71.064544 42.28787, -71.0645 42.287)
    factories.PotentialBreachFactory(
        the_geom=f"SRID=4326;LINESTRING({x} {y}, -71.064544 42.286)"
    )
    check = PotentialBreachStartEndCheck(
        models.PotentialBreach.the_geom, min_distance=1.0
    )
    invalid = check.get_invalid(session)
    if ok:
        assert len(invalid) == 0
    else:
        assert len(invalid) == 1


@pytest.mark.parametrize(
    "x,y,ok",
    [
        (-71.06452, 42.2874, True),  # exactly on other
        (-71.06452, 42.287401, False),  # too close to other
        (-71.0645, 42.287, True),  # far enough from other
    ],
)
def test_potential_breach_interdistance(session, x, y, ok):
    # channel geom: LINESTRING (-71.064544 42.28787, -71.0645 42.287)
    ref = factories.PotentialBreachFactory(
        the_geom="SRID=4326;LINESTRING(-71.06452 42.2874, -71.0646 42.286)"
    )
    factories.PotentialBreachFactory(
        the_geom=f"SRID=4326;LINESTRING({x} {y}, -71.064544 42.286)",
        channel=ref.channel,
    )
    check = PotentialBreachInterdistanceCheck(
        models.PotentialBreach.the_geom, min_distance=1.0
    )
    invalid = check.get_invalid(session)
    if ok:
        assert len(invalid) == 0
    else:
        assert len(invalid) == 1


def test_potential_breach_interdistance_other_channel(session):
    factories.PotentialBreachFactory(
        the_geom="SRID=4326;LINESTRING(-71.06452 42.2874, -71.0646 42.286)"
    )
    factories.PotentialBreachFactory(
        the_geom="SRID=4326;LINESTRING(-71.06452 42.287401, -71.064544 42.286)"
    )
    check = PotentialBreachInterdistanceCheck(
        models.PotentialBreach.the_geom, min_distance=1.0
    )
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


@pytest.mark.parametrize(
    "storage_area,time_step,expected_result,capacity",
    [
        (0.64, 30, 1, 12500),
        (600, 30, 0, 12500),
        (None, 30, 0, 12500),  # no storage --> open water --> no check
        (600, 30, 0, 0),
    ],
)
def test_pumpstation_storage_timestep(
    session, storage_area, time_step, expected_result, capacity
):
    connection_node = factories.ConnectionNodeFactory(storage_area=storage_area)
    factories.PumpstationFactory(
        connection_node_start=connection_node,
        start_level=-4,
        lower_stop_level=-4.78,
        capacity=capacity,
    )
    factories.GlobalSettingsFactory(sim_time_step=time_step)
    check = PumpStorageTimestepCheck(models.Pumpstation.capacity)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (1000, 0),  # total area = 1000 + 9000 = 10000 <= 10000; no error
        (1001, 1),  # total area = 1001 + 9000 = 10001 > 10000; error
    ],
)
def test_impervious_connection_node_inflow_area(session, value, expected_result):
    connection_node = factories.ConnectionNodeFactory()
    first_impervious_surface = factories.ImperviousSurfaceFactory(area=9000)
    second_impervious_surface = factories.ImperviousSurfaceFactory(area=value)
    factories.ImperviousSurfaceMapFactory(
        impervious_surface=first_impervious_surface, connection_node=connection_node
    )
    factories.ImperviousSurfaceMapFactory(
        impervious_surface=second_impervious_surface, connection_node=connection_node
    )
    check = ImperviousNodeInflowAreaCheck()
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "surface_number,expected_result",
    [
        (0, 1),
        (1, 0),
        (10, 0),
    ],
)
def test_inflow_no_features_impervious(session, surface_number, expected_result):
    # add fields
    factories.GlobalSettingsFactory()
    if surface_number > 0:
        factories.ImperviousSurfaceFactory.create_batch(size=surface_number)

    # test
    check = InflowNoFeaturesCheck(surface_table=models.ImperviousSurface)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "surface_number,expected_result",
    [
        (0, 1),
        (1, 0),
        (10, 0),
    ],
)
def test_inflow_no_features_pervious(session, surface_number, expected_result):
    # add fields
    factories.GlobalSettingsFactory()
    if surface_number > 0:
        factories.SurfaceFactory.create_batch(size=surface_number)

    # test
    check = InflowNoFeaturesCheck(surface_table=models.Surface)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (1000, 0),  # total area = 1000 + 9000 = 10000 <= 10000; no error
        (1001, 1),  # total area = 1001 + 9000 = 10001 > 10000; error
    ],
)
def test_pervious_connection_node_inflow_area(session, value, expected_result):
    factories.ConnectionNodeFactory(id=1)
    factories.SurfaceFactory(id=1, area=9000)
    factories.SurfaceFactory(id=2, area=value)
    factories.SurfaceMapFactory(surface_id=1, connection_node_id=1)
    factories.SurfaceMapFactory(surface_id=2, connection_node_id=1)
    check = PerviousNodeInflowAreaCheck()
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "surface_type",
    [("impervious"), ("pervious")],
)
@pytest.mark.parametrize(
    "connected_surfaces_count,expected_result",
    [
        (50, 0),
        (51, 1),
    ],
)
def test_connection_node_mapped_surfaces(
    session, surface_type, connected_surfaces_count, expected_result
):
    factories.ConnectionNodeFactory(id=1)
    if surface_type == "pervious":
        for i in range(connected_surfaces_count):
            factories.SurfaceMapFactory(connection_node_id=1, surface_id=i + 1)
    elif surface_type == "impervious":
        for i in range(connected_surfaces_count):
            factories.ImperviousSurfaceMapFactory(
                connection_node_id=1, impervious_surface_id=i + 1
            )
    check = NodeSurfaceConnectionsCheck(check_type=surface_type)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "configuration,expected_result",
    [
        ("closed", 0),
        ("open", 1),
    ],
)
def test_feature_closed_cross_section(session, configuration, expected_result):
    if configuration == "closed":
        shape = constants.CrossSectionShape.CLOSED_RECTANGLE
    else:
        shape = constants.CrossSectionShape.RECTANGLE
    cross_section_definition = factories.CrossSectionDefinitionFactory(
        shape=shape, height=1, width=1
    )
    factories.CulvertFactory(cross_section_definition=cross_section_definition)
    check = FeatureClosedCrossSectionCheck(models.Culvert.id)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "defined_area, max_difference, expected_result",
    [
        (1.5, 1.2, 0),
        (2, 1, 1),
        (1, 0.5, 1),
    ],
)
def test_defined_area(session, defined_area, max_difference, expected_result):
    # this geometry has an area of approximately 0.3778
    the_geom = "SRID=4326;MULTIPOLYGON(((4.7 52.5, 4.7 52.50001, 4.70001 52.50001, 4.70001 52.50001)))"
    factories.SurfaceFactory(area=defined_area, the_geom=the_geom)
    check = DefinedAreaCheck(models.Surface.area, max_difference=max_difference)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (None, 0),  # column not set, valid result
        (5, 1),  # column set, invalid result
    ],
)
def test_beta_columns(session, value, expected_result):
    factories.GlobalSettingsFactory(vegetation_drag_settings_id=value)
    check = BetaColumnsCheck(models.GlobalSetting.vegetation_drag_settings_id)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (
            constants.BoundaryType.RIEMANN,
            0,
        ),  # column not in beta columns, valid result
        (
            constants.BoundaryType.GROUNDWATERDISCHARGE,
            1,
        ),  # column in beta columns, invalid result
    ],
)
def test_beta_values(session, value, expected_result):
    beta_values = [
        constants.BoundaryType.GROUNDWATERLEVEL,
        constants.BoundaryType.GROUNDWATERDISCHARGE,
    ]
    factories.BoundaryConditions1DFactory(boundary_type=value)
    check = BetaValuesCheck(
        column=models.BoundaryCondition1D.boundary_type, values=beta_values
    )
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.skipif(
    condition=(not BETA_COLUMNS and not BETA_VALUES),
    reason="requires beta features to be defined in threedi-schema to run",
)
@pytest.mark.parametrize(
    "allow_beta_features, no_checks_expected",
    [
        (False, False),
        (True, True),
    ],
)
def test_beta_features_in_server(threedi_db, allow_beta_features, no_checks_expected):
    with mock.patch.object(ThreediDatabase, "schema"):
        model_checker = ThreediModelChecker(
            threedi_db, allow_beta_features=allow_beta_features
        )
    model_beta_checks = [
        check
        for check in model_checker.config.checks
        if type(check) in [BetaColumnsCheck, BetaValuesCheck]
    ]
    if no_checks_expected:
        assert len(model_beta_checks) == 0
    else:
        assert len(model_beta_checks) > 0


@pytest.mark.parametrize(
    "cols, shape, friction_type, result",
    [
        # single column defined: should fail
        (
            ["vegetation_height"],
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY,
            False,
        ),
        # both columns defined, but one empty: should fail
        (
            ["vegetation_height", "vegetation_stem_diameter"],
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY,
            False,
        ),
        # no columns defined: should pass
        (
            [],
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY,
            True,
        ),
        # both columns defined: should pass
        (
            [
                "vegetation_drag_coefficient",
                "vegetation_height",
                "vegetation_stem_diameter",
                "vegetation_stem_density",
            ],
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY,
            True,
        ),
        # shape is not included in check: should pass
        (
            ["vegetation_height"],
            constants.CrossSectionShape.RECTANGLE,
            constants.FrictionType.CHEZY,
            True,
        ),
        # friction type in not included in check: should pass
        (
            ["vegetation_height"],
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.MANNING,
            True,
        ),
    ],
)
def test_all_present_fixed_vegetation_parameters(
    session, cols, shape, friction_type, result
):
    definition = factories.CrossSectionDefinitionFactory(
        shape=shape,
        friction_values="1",
    )
    veg_args = {col: 1 for col in cols}
    factories.CrossSectionLocationFactory(
        definition=definition, friction_type=friction_type, **veg_args
    )
    check = AllPresentFixedVegetationParameters(
        column=models.CrossSectionLocation.vegetation_height
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


# TODO: add check for Variable...
@pytest.mark.parametrize(
    "cols, val, shape, friction_type, result",
    [
        # single column defined: should fail
        (
            ["vegetation_heights"],
            "1 2",
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY_CONVEYANCE,
            False,
        ),
        # both columns defined, but one empty: should fail
        (
            ["vegetation_heights", "vegetation_stem_diameters"],
            "1 2",
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY_CONVEYANCE,
            False,
        ),
        # no columns defined: should pass
        (
            [],
            "1 2",
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY_CONVEYANCE,
            True,
        ),
        # both columns defined: should pass
        (
            [
                "vegetation_drag_coefficients",
                "vegetation_heights",
                "vegetation_stem_diameters",
                "vegetation_stem_densities",
            ],
            "1 2",
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.CHEZY_CONVEYANCE,
            True,
        ),
        # shape is not included in check: should pass
        (
            ["vegetation_heights"],
            "1 2",
            constants.CrossSectionShape.RECTANGLE,
            constants.FrictionType.CHEZY_CONVEYANCE,
            True,
        ),
        # friction type in not included in check: should pass
        (
            ["vegetation_heights"],
            "1 2",
            constants.CrossSectionShape.TABULATED_YZ,
            constants.FrictionType.MANNING,
            True,
        ),
    ],
)
def test_all_present_variable_vegetation_parameters(
    session, cols, val, shape, friction_type, result
):
    veg_args = {col: val for col in cols}
    definition = factories.CrossSectionDefinitionFactory(
        shape=shape, friction_values="1 2", **veg_args
    )
    factories.CrossSectionLocationFactory(
        definition=definition, friction_type=friction_type
    )
    check = AllPresentVariableVegetationParameters(
        column=models.CrossSectionDefinition.vegetation_heights
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result
