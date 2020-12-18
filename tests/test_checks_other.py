import pytest

from threedi_modelchecker.checks.other import BankLevelCheck, valid_egg, \
    valid_rectangle, valid_circle, ConnectionNodesLength, OpenChannelsWithNestedNewton
from threedi_modelchecker.checks.other import CrossSectionShapeCheck
from threedi_modelchecker.checks.other import TimeseriesCheck
from threedi_modelchecker.checks.other import valid_tabulated_shape
from threedi_modelchecker.threedi_model import models, constants
from . import factories
from .factories import BoundaryConditions2DFactory


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
    wrong = factories.CrossSectionLocationFactory(
        channel=channel, bank_level=None
    )
    factories.CrossSectionLocationFactory(
        channel=channel, bank_level=1.0
    )
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


def test_get_invalid_cross_section_shapes(session):
    factories.CrossSectionDefinitionFactory(
        width="1", height="1", shape=constants.CrossSectionShape.RECTANGLE
    )
    factories.CrossSectionDefinitionFactory(
        width="1", height=None, shape=constants.CrossSectionShape.CIRCLE
    )
    factories.CrossSectionDefinitionFactory(
        width="1 2", height="0 2",
        shape=constants.CrossSectionShape.TABULATED_TRAPEZIUM
    )

    coss_section_check = CrossSectionShapeCheck()
    invalid_rows = coss_section_check.get_invalid(session)
    assert len(invalid_rows) == 0


def test_get_invalid_cross_section_shapes_egg_with_none_height_width(session):
    factories.CrossSectionDefinitionFactory(
        width=None, height=None, shape=constants.CrossSectionShape.EGG
    )
    cross_section_check = CrossSectionShapeCheck()
    invalid_rows = cross_section_check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_get_invalid_cross_section_shapes_rectangle_with_null(session):
    factories.CrossSectionDefinitionFactory(
        width=None, height=None, shape=constants.CrossSectionShape.RECTANGLE
    )
    cross_section_check = CrossSectionShapeCheck()
    invalid_rows = cross_section_check.get_invalid(session)
    assert len(invalid_rows) == 1


def test_valid_rectangle():
    assert valid_rectangle(width="1", height="2")


def test_valid_rectangle_none_value():
    assert not valid_rectangle(width=None, height="2")


def test_valid_rectangle_negative_value():
    assert not valid_rectangle(width="-1", height="2")


def test_valid_circle():
    assert valid_circle("3")


def test_valid_circle_none_value():
    assert not valid_circle(None)


def test_valid_circle_negative_value():
    assert not valid_circle("-3")


def test_valid_egg_none_value():
    assert not valid_egg(width=None)


def test_valid_egg_negative_value():
    assert not valid_egg(width="-1")


def test_valid_egg_zero_value():
    assert not valid_egg(width="0")


def test_valid_egg_positive_value():
    assert valid_egg(width="1")


def test_valid_tabulated_shape():
    width = "0 1 2 3"
    height = "0 1 2 3"
    assert valid_tabulated_shape(width, height)


def test_valid_tabulated_shape_none():
    assert not valid_tabulated_shape(None, None)


def test_valid_tabulated_shape_empty():
    assert not valid_tabulated_shape("", "")


def test_valid_tabulated_shape_unequal_length():
    width = "1 2"
    height = "1 2 3"
    assert not valid_tabulated_shape(width, height)


def test_valid_tabulated_shape_invalid_char():
    width = "1 2"
    height = "1 a"
    assert not valid_tabulated_shape(width, height)


def test_tabulated_shape_valid123():
    width = "7 7 0"
    height = "0 2.25 2.25"
    assert valid_tabulated_shape(width, height)


def test_tabulated_shape_invalid_height_not_start_0():
    width = "0.5106338 0.8793753 1.109911 1.279277 1.409697 1.511286 1.589584 " \
            "1.647911 1.688341 1.71214 1.72 1.72"
    height = "0.831 0.749 0.667 0.585 0.503 0.421 0.338 0.256 0.174 0.092 0 0.01"
    assert not valid_tabulated_shape(width, height)


def test_tabulated_shape_invalid_non_increasing_height():
    width = "1 2 3"
    height = "0 2 1"
    assert not valid_tabulated_shape(width, height)


def test_timeseries_check(session):
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
    BoundaryConditions2DFactory(
        timeseries="0,-0.5\n1,1.4\n2,4.0"
    )
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
        )
    )
    weir_too_short = factories.WeirFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222938832999598 -0.13872236685816669)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=4326;POINT(-0.38222930900909202 -0.13872236685816669)"
        )
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05
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
        )
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05
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
        )
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05
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
        connection_node_end=None
    )

    check_length = ConnectionNodesLength(
        column=models.Weir.id,
        start_node=models.Weir.connection_node_start,
        end_node=models.Weir.connection_node_end,
        min_distance=0.05
    )

    errors = check_length.get_invalid(session)
    assert len(errors) == 0


def test_open_channels_with_nested_newton(session):
    factories.NumericalSettingsFactory(use_of_nested_newton=0)
    channel = factories.ChannelFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=28992;POINT(-71.064544 42.28787)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=28992;POINT(-71.0645 42.287)"
        ),
        the_geom="SRID=28992;LINESTRING(-71.064544 42.28787, -71.0645 42.287)",
    )
    open_definition = factories.CrossSectionDefinitionFactory(
        shape=constants.CrossSectionShape.TABULATED_TRAPEZIUM,
        width="1 0"
    )
    factories.CrossSectionLocationFactory(
        channel=channel, definition=open_definition,
        the_geom="SRID=28992;POINT(-71.0645 42.287)"
    )

    channel2 = factories.ChannelFactory(
        connection_node_start=factories.ConnectionNodeFactory(
            the_geom="SRID=28992;POINT(-71.064544 42.28787)"
        ),
        connection_node_end=factories.ConnectionNodeFactory(
            the_geom="SRID=28992;POINT(-71.0645 42.287)"
        ),
        the_geom="SRID=28992;LINESTRING(-71.064544 42.28787, -71.0645 42.287)",
    )
    open_definition_egg = factories.CrossSectionDefinitionFactory(
        shape=constants.CrossSectionShape.EGG,
    )
    factories.CrossSectionLocationFactory(
        channel=channel2, definition=open_definition_egg,
        the_geom="SRID=28992;POINT(-71.0645 42.287)"
    )

    check = OpenChannelsWithNestedNewton()

    errors = check.get_invalid(session)
    assert len(errors) == 2
