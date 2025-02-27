from unittest import mock

import pytest
from sqlalchemy import select, text
from threedi_schema import constants, models, ThreediDatabase
from threedi_schema.beta_features import BETA_COLUMNS, BETA_VALUES

from threedi_modelchecker.checks.other import (
    AllPresentVegetationParameters,
    BetaColumnsCheck,
    BetaValuesCheck,
    ChannelManholeLevelCheck,
    ConnectionNodesDistance,
    ConnectionNodesLength,
    ControlHasSingleMeasureVariable,
    CorrectAggregationSettingsExist,
    CrossSectionSameConfigurationCheck,
    DefinedAreaCheck,
    DWFDistributionCSVFormatCheck,
    DWFDistributionLengthCheck,
    DWFDistributionSumCheck,
    FeatureClosedCrossSectionCheck,
    InflowNoFeaturesCheck,
    MaxOneRecordCheck,
    ModelEPSGCheckProjected,
    ModelEPSGCheckUnits,
    ModelEPSGCheckValid,
    NodeSurfaceConnectionsCheck,
    OpenChannelsWithNestedNewton,
    PotentialBreachInterdistanceCheck,
    PotentialBreachStartEndCheck,
    PumpStorageTimestepCheck,
    SpatialIndexCheck,
    SurfaceNodeInflowAreaCheck,
    TableControlActionTableCheckDefault,
    TableControlActionTableCheckDischargeCoefficients,
    TagsValidCheck,
    Use0DFlowCheck,
    UsedSettingsPresentCheck,
    UsedSettingsPresentCheckSingleTable,
)
from threedi_modelchecker.model_checks import ThreediModelChecker

from . import factories

SRID = 28992
POINT1 = "142742 473443"
POINT2 = "142743 473443"  # POINT1 + 1 meter
POINT3 = "142747 473443"  # POINT1 + 5 meter


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
    factories.ModelSettingsFactory(id=1)
    factories.AggregationSettingsFactory(
        aggregation_method=constants.AggregationMethod.CUMULATIVE,
        flow_variable=constants.FlowVariable.PUMP_DISCHARGE,
    )
    check = CorrectAggregationSettingsExist(
        aggregation_method=aggregation_method, flow_variable=flow_variable
    )
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


def test_connection_nodes_length(session):
    factories.ModelSettingsFactory()
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.ConnectionNodeFactory(id=2, geom=f"SRID={SRID};POINT({POINT2})")
    factories.WeirFactory(
        connection_node_id_start=1,
        connection_node_id_end=2,
    )
    weir_too_short = factories.WeirFactory(
        connection_node_id_start=1,
        connection_node_id_end=1,
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_id_start,
        end_node=models.Weir.connection_node_id_end,
        min_distance=0.01,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 1
    assert errors[0].id == weir_too_short.id


def test_connection_nodes_length_missing_start_node(session):
    factories.ModelSettingsFactory()
    factories.WeirFactory(connection_node_id_start=1, connection_node_id_end=2)
    factories.ConnectionNodeFactory(id=2)
    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_id_start,
        end_node=models.Weir.connection_node_id_end,
        min_distance=0.05,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 0


def test_connection_nodes_length_missing_end_node(session):
    if session.bind.name == "postgresql":
        pytest.skip("Postgres only accepts coords in epsg 4326")
    factories.ModelSettingsFactory()
    factories.WeirFactory(connection_node_id_start=1, connection_node_id_end=2)
    factories.ConnectionNodeFactory(id=1)
    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_id_start,
        end_node=models.Weir.connection_node_id_end,
        min_distance=0.05,
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 0


def test_open_channels_with_nested_newton(session):
    factories.NumericalSettingsFactory(use_nested_newton=0)
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({POINT1})")
    factories.ConnectionNodeFactory(id=2, geom=f"SRID={SRID};POINT({POINT2})")
    factories.ChannelFactory(
        id=1,
        connection_node_id_start=1,
        connection_node_id_end=2,
        geom=f"SRID={SRID};LINESTRING({POINT1}, {POINT2})",
    )
    factories.CrossSectionLocationFactory(
        channel_id=1,
        cross_section_shape=constants.CrossSectionShape.TABULATED_TRAPEZIUM,
        cross_section_table="0,1\n1,0",
        geom=f"SRID={SRID};POINT({POINT2})",
    )
    factories.ChannelFactory(
        id=2,
        connection_node_id_start=1,
        connection_node_id_end=2,
        geom=f"SRID={SRID};LINESTRING({POINT1}, {POINT2})",
    )
    factories.CrossSectionLocationFactory(
        channel_id=2,
        geom=f"SRID={SRID};POINT({POINT2})",
        cross_section_shape=constants.CrossSectionShape.EGG,
    )

    check = OpenChannelsWithNestedNewton(column=models.CrossSectionLocation.id)

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
    factories.ConnectionNodeFactory(
        id=1,
        geom=f"SRID={SRID};POINT({POINT1})",
        bottom_level=manhole_level,
    )
    factories.ConnectionNodeFactory(
        id=2,
        geom=f"SRID={SRID};POINT({POINT2})",
        bottom_level=manhole_level,
    )
    factories.ChannelFactory(
        id=1,
        geom=f"SRID={SRID};LINESTRING({POINT1}, {POINT2})",
        connection_node_id_start=1,
        connection_node_id_end=2,
    )
    # starting cross-section location
    factories.CrossSectionLocationFactory(
        geom=f"SRID={SRID};POINT(142742.25 473443)",
        reference_level=starting_reference_level,
        channel_id=1,
    )
    # ending cross-section location
    factories.CrossSectionLocationFactory(
        geom=f"SRID={SRID};POINT(142743.25 473443)",
        reference_level=ending_reference_level,
        channel_id=1,
    )
    check = ChannelManholeLevelCheck(nodes_to_check=manhole_location)
    errors = check.get_invalid(session)
    assert len(errors) == errors_number


@pytest.mark.parametrize("other_x, valid", [(142740.05, False), (142740.15, True)])
def test_node_distance_alt(session, other_x, valid):
    factories.ConnectionNodeFactory(id=0, geom=f"SRID={SRID};POINT(142740 473443)")
    factories.ConnectionNodeFactory(id=1, geom=f"SRID={SRID};POINT({other_x} 473443)")
    # Note that the test uses plain sqlite, so this needs to be committed
    session.commit()
    check = ConnectionNodesDistance(minimum_distance=0.1)
    invalid = check.get_invalid(session)
    assert (len(invalid) == 0) == valid
    # Remove connection nodes
    session.query(models.ConnectionNode).delete()
    session.commit()


class TestCrossSectionSameConfiguration:
    @pytest.mark.parametrize("sep, expected", [(",", "1"), ("\n", "1,2")])
    def test_get_first_in_str(self, session, sep, expected):
        factories.CrossSectionLocationFactory(
            cross_section_table="1,2\n3,4",
        )
        check = CrossSectionSameConfigurationCheck(models.CrossSectionLocation.id)
        result = check.get_first_in_str(
            models.CrossSectionLocation.cross_section_table, sep=sep
        )
        assert session.execute(select(result)).fetchall()[0][0] == expected

    @pytest.mark.parametrize("sep, expected", [(",", "4"), ("\n", "3,4")])
    def test_get_last_in_str(self, session, sep, expected):
        factories.CrossSectionLocationFactory(
            cross_section_table="1,2\n3,4",
        )
        check = CrossSectionSameConfigurationCheck(models.CrossSectionLocation.id)
        result = check.get_last_in_str(
            models.CrossSectionLocation.cross_section_table, sep=sep
        )
        assert session.execute(select(result)).fetchall()[0][0] == expected

    @pytest.mark.parametrize(
        "method_name, expected",
        [
            ("first_row_width", 1.0),
            ("first_row_height", 2.0),
            ("last_row_width", 3.0),
            ("last_row_height", 4.0),
        ],
    )
    def test_row_values(self, session, method_name, expected):
        factories.CrossSectionLocationFactory(
            cross_section_table="1,2\n3,4",
        )
        check = CrossSectionSameConfigurationCheck(models.CrossSectionLocation.id)
        result = getattr(check, method_name)()
        assert session.execute(select(result)).fetchall()[0][0] == expected

    @pytest.mark.parametrize(
        "shape, table, expected",
        [
            (0, "3,4\n3,4", "closed"),
            (1, "3,4\n3,4", "open"),
            (2, "3,4\n3,4", "closed"),
            (3, "3,4\n3,4", "closed"),
            (4, "3,4\n3,4", "open"),
            (5, "3,4\n0,1", "closed"),
            (6, "3,4\n3,4", "open"),
            (7, "3,4\n3,4", "closed"),
            (7, "1,3\n1,4", "open"),
            (8, "3,4\n3,4", "closed"),
        ],
    )
    def test_configuration_type(self, session, shape, table, expected):
        factories.CrossSectionLocationFactory(
            cross_section_shape=shape,
            cross_section_table=table,
        )
        check = CrossSectionSameConfigurationCheck(models.CrossSectionLocation.id)

        cross_sections = (
            select(
                models.CrossSectionLocation.cross_section_shape,
                check.first_row_width().label("first_width"),
                check.first_row_height().label("first_height"),
                check.last_row_width().label("last_width"),
                check.last_row_height().label("last_height"),
            )
            .select_from(models.CrossSectionLocation)
            .subquery()  # Added this line
        )
        # Without this, there is nothing that check.configuration_type can use
        session.execute(select(cross_sections))
        config_types = select(
            check.configuration_type(
                shape=cross_sections.c.cross_section_shape,
                first_width=cross_sections.c.first_width,
                last_width=cross_sections.c.last_width,
                first_height=cross_sections.c.first_height,
                last_height=cross_sections.c.last_height,
            ).label("configuration"),
        )
        assert session.execute(config_types).fetchall()[0][0] == expected


# cases to test: tabulated and non tabulated, everything else is covered above
@pytest.mark.parametrize(
    "shape, width, height, table, same_channels, ok",
    [
        # --- closed cross-sections ---
        # shapes 0, 2, 3 and 8 are always closed
        (0, 3, 4, None, True, False),
        # shape 7 is closed if the first and last (width, height) coordinates are the same
        (
            7,
            None,
            None,
            "2,3\n4.142,0.174\n5.143,0.348\n5.143,0.522\n5.869,0.696\n2,3",
            True,
            False,
        ),
        # shape 7 is open if the first and last (width, height) coordinates are not the same
        (
            7,
            None,
            None,
            "2,4\n4.142,0.174\n5.143,0.348\n5.143,0.522\n5.869,0.696\n3,4",
            True,
            True,
        ),
        # Bad data, could result in false positive but the real issue is covered by other checks
        (7, None, None, "foo", True, False),
        # Check on different channels
        # this should fail if the cross-sections are on the same channel, but pass on different channels
        (0, 3, 4, None, False, True),
    ],
)
def test_cross_section_same_configuration(
    session, shape, width, height, table, same_channels, ok
):
    """
    This test checks two cross-sections on a channel against each other; they should both be open or both be closed.
    In this test, the first cross-section has been set to always be open.
    Therefore, the channel should be invalid when the second cross-section is closed, and valid when it is open.
    """
    factories.ChannelFactory(
        id=1,
    )
    factories.ChannelFactory(
        id=2,
    )
    # shape 1 is always open
    factories.CrossSectionLocationFactory(
        channel_id=1,
        cross_section_shape=1,
        cross_section_width=3,
        cross_section_height=4,
    )
    # the second one is parametrised
    factories.CrossSectionLocationFactory(
        channel_id=1 if same_channels else 2,
        cross_section_shape=shape,
        cross_section_width=width,
        cross_section_height=height,
        cross_section_table=table,
    )
    errors = CrossSectionSameConfigurationCheck(column=models.Channel.id).get_invalid(
        session
    )
    assert len(errors) == (0 if ok else 1)


def test_spatial_index_ok(session):
    check = SpatialIndexCheck(models.ConnectionNode.geom)
    invalid = check.get_invalid(session)
    assert len(invalid) == 0


def test_spatial_index_disabled(empty_sqlite_v4):
    session = empty_sqlite_v4.get_session()
    session.execute(text("DROP TABLE IF EXISTS rtree_connection_nodes_geom"))
    check = SpatialIndexCheck(models.ConnectionNode.geom)
    invalid = check.get_invalid(session)
    assert len(invalid) == 1


@pytest.mark.parametrize(
    "start,ok",
    [
        ("142742 473443", True),  # at start
        ("142747 473448", True),  # at end
        ("142744.5 473445.5", True),  # middle
        ("142742 473443.01", False),  # close to start
        ("142747 473447.99", False),  # close to end
    ],
)
def test_potential_breach_start_end(session, start, ok):
    # channel geom: "SRID={SRID}};LINESTRING (142742 473443, 142747 473448)"
    factories.ChannelFactory(id=1)
    factories.PotentialBreachFactory(
        geom=f"SRID={SRID};LINESTRING({start}, 142750 473450)", channel_id=1
    )
    check = PotentialBreachStartEndCheck(models.PotentialBreach.geom, min_distance=1.0)
    invalid = check.get_invalid(session)
    if ok:
        assert len(invalid) == 0
    else:
        assert len(invalid) == 1


@pytest.mark.parametrize(
    "start,channel_id,ok",
    [
        (POINT1, 1, True),  # exactly on other
        ("142742.5 473443.5", 1, False),  # too close to other
        ("142742.5 473443.5", 2, True),  # too close to other but other channel
        ("142740 473440", 1, True),  # far enough from other
    ],
)
def test_potential_breach_interdistance(session, start, channel_id, ok):
    # channel geom: "SRID=28992;LINESTRING (142742 473443, 142747 473448)"
    factories.ChannelFactory(id=1)
    factories.ChannelFactory(id=2)
    factories.PotentialBreachFactory(
        geom=f"SRID={SRID};LINESTRING({POINT1}, {POINT3})", channel_id=1
    )
    factories.PotentialBreachFactory(
        geom=f"SRID={SRID};LINESTRING({start}, 142737 473438)", channel_id=channel_id
    )
    check = PotentialBreachInterdistanceCheck(
        models.PotentialBreach.geom, min_distance=1.0
    )
    invalid = check.get_invalid(session)
    if ok:
        assert len(invalid) == 0
    else:
        assert len(invalid) == 1


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
    factories.ConnectionNodeFactory(storage_area=storage_area, id=1)
    factories.PumpFactory(
        connection_node_id=1,
        start_level=-4,
        lower_stop_level=-4.78,
        capacity=capacity,
    )
    factories.TimeStepSettingsFactory(time_step=time_step)
    check = PumpStorageTimestepCheck(models.Pump.capacity)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (1000, 0),  # total area = 1000 + 9000 = 10000 <= 10000; no error
        (1001, 1),  # total area = 1001 + 9000 = 10001 > 10000; error
    ],
)
def test_surface_connection_node_inflow_area(session, value, expected_result):
    connection_node = factories.ConnectionNodeFactory(id=1)
    first_surface = factories.SurfaceFactory(id=1, area=9000)
    second_surface = factories.SurfaceFactory(id=2, area=value)
    factories.SurfaceMapFactory(
        surface_id=first_surface.id, connection_node_id=connection_node.id
    )
    factories.SurfaceMapFactory(
        surface_id=second_surface.id, connection_node_id=connection_node.id
    )
    check = SurfaceNodeInflowAreaCheck()
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
    factories.ModelSettingsFactory()
    if surface_number > 0:
        factories.SurfaceFactory.create_batch(size=surface_number)

    # Only test this for surface because InflowNoFeaturesCheck only uses table length and not table contents
    check = InflowNoFeaturesCheck(feature_table=models.Surface)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "connected_surfaces_count,expected_result",
    [
        (50, 0),
        (51, 1),
    ],
)
def test_connection_node_mapped_surfaces(
    session, connected_surfaces_count, expected_result
):
    factories.ConnectionNodeFactory(id=1)
    for i in range(connected_surfaces_count):
        factories.SurfaceMapFactory(connection_node_id=1, surface_id=i + 1)
    check = NodeSurfaceConnectionsCheck()
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "shape,expected_result",
    [
        (constants.CrossSectionShape.CLOSED_RECTANGLE, 0),
        (constants.CrossSectionShape.RECTANGLE, 1),
    ],
)
def test_feature_closed_cross_section(session, shape, expected_result):
    factories.CrossSectionLocationFactory(
        cross_section_shape=shape, cross_section_width=1, cross_section_height=1
    )
    check = FeatureClosedCrossSectionCheck(models.CrossSectionLocation.id)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "defined_area, max_difference, expected_result",
    [
        (1.2, 0.5, 0),
        (1, 1, 0),
        (2.1, 1, 1),
        (1.6, 0.5, 1),
    ],
)
def test_defined_area(session, defined_area, max_difference, expected_result):
    # create square polygon with area 1
    x0 = int(POINT1.split()[0])
    y0 = int(POINT1.split()[1])
    geom = f"SRID={SRID};POLYGON(({x0} {y0}, {x0 + 1} {y0}, {x0 + 1} {y0 + 1}, {x0} {y0 + 1}, {x0} {y0}))"

    factories.SurfaceFactory(area=defined_area, geom=geom)
    check = DefinedAreaCheck(models.Surface.area, max_difference=max_difference)
    invalid = check.get_invalid(session)
    assert len(invalid) == expected_result


@pytest.mark.parametrize(
    "value,expected_result",
    [
        (None, 0),  # column not set, valid result
        (True, 1),  # column set, invalid result
    ],
)
def test_beta_columns(session, value, expected_result):
    # Note that the BetaColumnsCheck is just a check for value=None.
    # So it can be mocked with any nullable column
    factories.ModelSettingsFactory(friction_averaging=value)
    check = BetaColumnsCheck(models.ModelSettings.friction_averaging)
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
    factories.BoundaryConditions1DFactory(type=value)
    check = BetaValuesCheck(column=models.BoundaryCondition1D.type, values=beta_values)
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
    veg_args = {col: 1 for col in cols}
    factories.CrossSectionLocationFactory(
        cross_section_shape=shape,
        cross_section_friction_values="1",
        friction_type=friction_type,
        **veg_args,
    )
    check = AllPresentVegetationParameters(
        column=models.CrossSectionLocation.vegetation_height
    )
    invalid_rows = check.get_invalid(session)
    assert (len(invalid_rows) == 0) == result


@pytest.mark.parametrize(
    "use_0d_inflow",
    [
        constants.InflowType.NO_INFLOW,
        constants.InflowType.SURFACE,
        constants.InflowType.IMPERVIOUS_SURFACE,
    ],
)
@pytest.mark.parametrize("add_surface", [True, False])
def test_use_0d_flow_check(session, use_0d_inflow: int, add_surface: bool):
    factories.SimulationTemplateSettingsFactory(use_0d_inflow=use_0d_inflow)
    if add_surface:
        factories.SurfaceFactory()
    if use_0d_inflow == constants.InflowType.NO_INFLOW:
        nof_invalid_expected = 0
    else:
        nof_invalid_expected = 0 if add_surface else 1
    check = Use0DFlowCheck()
    assert (len(check.get_invalid(session))) == nof_invalid_expected


@pytest.mark.parametrize("use_setting", [True, False])
@pytest.mark.parametrize("add_setting", [True, False])
def test_used_settings_present_check_single_table(session, use_setting, add_setting):
    nof_invalid_expected = 1 if use_setting and not add_setting else 0
    factories.ModelSettingsFactory(use_vegetation_drag_2d=use_setting)
    if add_setting:
        factories.VegetationDragFactory()
    check = UsedSettingsPresentCheckSingleTable(
        column=models.ModelSettings.use_vegetation_drag_2d,
        settings_table=models.VegetationDrag2D,
    )
    assert len(check.get_invalid(session)) == nof_invalid_expected


@pytest.mark.parametrize("use_setting", [True, False])
@pytest.mark.parametrize("add_surface", [True, False])
@pytest.mark.parametrize("add_dwf", [True, False])
def test_used_settings_present_check(session, use_setting, add_surface, add_dwf):
    nof_invalid_expected = 1 if use_setting and not (add_surface and add_dwf) else 0
    factories.SimulationTemplateSettingsFactory(use_0d_inflow=use_setting)
    if add_surface:
        factories.SurfaceFactory()
    if add_dwf:
        factories.DryWeatherFlowFactory()
    check = UsedSettingsPresentCheck(
        column=models.SimulationTemplateSettings.use_0d_inflow,
        settings_tables=[models.Surface, models.DryWeatherFlow],
    )
    assert len(check.get_invalid(session)) == nof_invalid_expected


@pytest.mark.parametrize(
    "nof_rows_to_add, fail",
    [
        (1, False),
        # add to many rows
        (2, True),
        # empty table
        (0, False),
    ],
)
def test_max_one_record_check(session, nof_rows_to_add: int, fail: bool):
    for _ in range(nof_rows_to_add):
        factories.ModelSettingsFactory()
    check = MaxOneRecordCheck(column=models.ModelSettings.id)
    nof_invalid = len(check.get_invalid(session))
    assert (nof_invalid > 0) == fail


def test_tags_valid(session):
    factories.TagsFactory(id=1, description="foo")
    factories.DryWeatherFlowFactory(tags="1,2")
    check = TagsValidCheck(column=models.DryWeatherFlow.tags)
    assert len(check.get_invalid(session)) == 1
    factories.TagsFactory(id=2, description="bar")
    assert len(check.get_invalid(session)) == 0


@pytest.mark.parametrize(
    "action_table, valid",
    [
        ("1,2", True),
        ("1,2\n3,4", True),
        ("2,3\n3,4\n", True),
        ("1.0,2", True),
        ("1,2.1", True),
        ("1;2", False),
        ("1,2 3", False),
        ("1,2,3", False),
    ],
)
def test_control_table_action_table_check_default(session, action_table, valid):
    factories.TableControlFactory(
        action_table=action_table,
        action_type=constants.TableControlActionTypes.set_capacity,
    )
    check = TableControlActionTableCheckDefault()
    assert (len(check.get_invalid(session)) == 0) == valid


@pytest.mark.parametrize(
    "action_table, valid",
    [
        ("1,2 3", True),
        ("1,2 3\n3,4 5", True),
        ("2,3 3\n3,4 5\n", True),
        ("1.0,2 3", True),
        ("1,2.1 3", True),
        ("1,2.1 3", True),
        ("1,2.1 3.3", True),
        ("1,2", False),
        ("1;2 3", False),
        ("1,2,3", False),
        ("1,2 3 4", False),
    ],
)
def test_control_table_action_table_check_discharge_coefficients(
    session, action_table, valid
):
    factories.TableControlFactory(
        action_table=action_table,
        action_type=constants.TableControlActionTypes.set_discharge_coefficients,
    )
    check = TableControlActionTableCheckDischargeCoefficients()
    assert (len(check.get_invalid(session)) == 0) == valid


@pytest.mark.parametrize(
    "measure_variables, valid",
    [
        (
            [
                constants.MeasureVariables.waterlevel,
                constants.MeasureVariables.waterlevel,
            ],
            True,
        ),
        (
            [constants.MeasureVariables.waterlevel, constants.MeasureVariables.volume],
            False,
        ),
    ],
)
def test_control_has_single_measure_variable(session, measure_variables, valid):
    factories.TableControlFactory(id=1)
    for i, measure_variable in enumerate(measure_variables, 1):
        factories.MeasureMapFactory(
            control_id=1, measure_location_id=i, control_type="table"
        )
        factories.MeasureLocationFactory(id=i, measure_variable=measure_variable)
    check = ControlHasSingleMeasureVariable(control_model=models.TableControl)
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid


@pytest.mark.parametrize("distribution, valid", [("1,2", True), ("1 2", False)])
def test_dwf_distribution_csv_format_check(session, distribution, valid):
    factories.DryWeatherFlowDistributionFactory(distribution=distribution)
    check = DWFDistributionCSVFormatCheck()
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid


@pytest.mark.parametrize(
    "distribution, valid",
    [
        (
            "3,1.5,1,1,0.5,0.5,2.5,8,7.5,6,5.5,5,4.5,4,4,3.5,3.5,4,5.5,8,7,5.5,4.5,4",
            True,
        ),
        ("1,2", False),
    ],
)
def test_dwf_distribution_length_check(session, distribution, valid):
    factories.DryWeatherFlowDistributionFactory(distribution=distribution)
    check = DWFDistributionLengthCheck()
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid


@pytest.mark.parametrize(
    "distribution, valid",
    [
        (
            "3,1.5,1,1,0.5,0.5,2.5,8,7.5,6,5.5,5,4.5,4,4,3.5,3.5,4,5.5,8,7,5.5,4.5,4",
            True,
        ),
        (
            "3.33,1.5,1.33,0.33,0.5,0.5,2.5,8,7.5,6,5.5,5,4.5,4,4,3.5,3.5,4,5.5,8,7,5.5,4.5,4",
            True,
        ),
        (
            "3.3,1.5,1.3,0.3,0.5,0.5,2.5,8,7.5,6,5.5,5,4.5,4,4,3.5,3.5,4,5.5,8,7,5.5,4.5,4",
            False,
        ),
        (
            "3,1.5,1,1,0.5,0.5,2.5,8,7.5,6,5.5,5,4.5,4,4,3.5,3.5,4,5.5,8,7,5.5,4.5,40",
            False,
        ),
    ],
)
def test_dwf_distribution_sum_check(session, distribution, valid):
    factories.DryWeatherFlowDistributionFactory(distribution=distribution)
    check = DWFDistributionSumCheck()
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid


@pytest.mark.parametrize(
    "ref_epsg, valid",
    [
        (28992, True),
        (999999, False),
    ],
)
def test_model_epsg_check_valid(session, ref_epsg, valid):
    factories.ModelSettingsFactory()
    session.model_checker_context.epsg_ref_code = ref_epsg
    check = ModelEPSGCheckValid()
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid


@pytest.mark.parametrize(
    "ref_epsg, valid",
    [
        (28992, True),
        (4326, False),
        (None, True),  # skip check when there is no epsg
    ],
)
def test_model_epsg_check_projected(session, ref_epsg, valid):
    factories.ModelSettingsFactory()
    session.model_checker_context.epsg_ref_code = ref_epsg
    check = ModelEPSGCheckProjected()
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid


@pytest.mark.parametrize(
    "ref_epsg, valid",
    [
        (28992, True),
        (4326, False),
        (None, True),  # skip check when there is no epsg
    ],
)
def test_model_epsg_check_units(session, ref_epsg, valid):
    factories.ModelSettingsFactory()
    session.model_checker_context.epsg_ref_code = ref_epsg
    check = ModelEPSGCheckUnits()
    invalids = check.get_invalid(session)
    assert (len(invalids) == 0) == valid
