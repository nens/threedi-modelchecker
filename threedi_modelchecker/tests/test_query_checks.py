import pytest
from threedi_schema import constants, models

# Import all checks created in the config
from threedi_modelchecker.config import CHECKS

from . import factories


def get_checks_by_number(check_number):
    return [c for c in CHECKS if c.error_code == check_number]


def run_query_check_by_number(session, check_number):
    check = next(c for c in CHECKS if c.error_code == check_number)
    return check.get_invalid(session)


@pytest.mark.parametrize(
    "exchange_type, has_1d_element, expected_invalid_count",
    [
        (constants.CalculationTypeNode.EMBEDDED, False, 0),
        (constants.CalculationTypeNode.EMBEDDED, True, 0),
        (constants.CalculationTypeNode.ISOLATED, False, 0),
        (constants.CalculationTypeNode.ISOLATED, True, 0),
        (constants.CalculationTypeNode.CONNECTED, False, 1),
        (constants.CalculationTypeNode.CONNECTED, True, 0),
    ],
)
def test_standalone_pump_connection_node_not_embedded_needs_1d_element(
    session, exchange_type, has_1d_element, expected_invalid_count
):
    cn_pump = factories.ConnectionNodeFactory(id=1, exchange_type=exchange_type)
    cn_other = factories.ConnectionNodeFactory(id=2)
    factories.PumpFactory(id=1, connection_node_id=cn_pump.id)
    factories.PumpMapFactory(pump_id=1, connection_node_id_end=cn_other.id)
    if has_1d_element:
        factories.CulvertFactory(
            connection_node_id_start=cn_pump.id,
            connection_node_id_end=cn_other.id,
        )

    result = run_query_check_by_number(session, 254)
    assert len(result) == expected_invalid_count


@pytest.mark.parametrize(
    "pump_connection_node_id,pump_map_connection_node_id_end,expected_invalid_count",
    [
        (1, 1, 1),
        (1, 2, 0),
    ],
)
def test_pump_cannot_be_connected_to_itself_check_253(
    session,
    pump_connection_node_id,
    pump_map_connection_node_id_end,
    expected_invalid_count,
):
    factories.PumpFactory(id=10, connection_node_id=pump_connection_node_id)
    factories.PumpMapFactory(
        pump_id=10,
        connection_node_id_end=pump_map_connection_node_id_end,
    )
    all_checks = get_checks_by_number(253)
    pump_check = next(
        c for c in all_checks if c.column == models.Pump.connection_node_id
    )
    result = pump_check.get_invalid(session)
    assert len(result) == expected_invalid_count


@pytest.mark.parametrize(
    "pump_cn_id, pump_map_cn_id, expected_invalid_count",
    [(1, 1, 0), (10, 1, 1), (1, 10, 1)],
)
def test_boundary_condition_cannot_be_connected_to_a_pump(
    session, pump_cn_id, pump_map_cn_id, expected_invalid_count
):
    factories.BoundaryConditions1DFactory(connection_node_id=10)
    factories.PumpFactory(connection_node_id=pump_cn_id)
    factories.PumpMapFactory(connection_node_id_end=pump_map_cn_id)
    result = run_query_check_by_number(session, 71)
    assert len(result) == expected_invalid_count
