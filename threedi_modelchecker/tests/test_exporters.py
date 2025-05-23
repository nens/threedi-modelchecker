from unittest.mock import MagicMock

import pytest
from geoalchemy2.elements import WKBElement

from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.exporters import (
    export_with_geom,
    generate_csv_table,
    generate_rst_table,
)


@pytest.fixture
def fake_check_warning():
    fake_check = MagicMock()
    fake_check.level = CheckLevel.WARNING
    fake_check.error_code = 2
    fake_check.description.return_value = (
        "This sample message has code 2 and level WARNING"
    )
    return fake_check


@pytest.fixture
def fake_check_error():
    fake_check = MagicMock()
    fake_check.level = CheckLevel.ERROR
    fake_check.error_code = 1234
    fake_check.description.return_value = (
        "This sample message has code 1234 and level ERROR"
    )
    return fake_check


@pytest.fixture
def fake_check_info():
    fake_check = MagicMock()
    fake_check.level = CheckLevel.INFO
    fake_check.error_code = 12
    fake_check.description.return_value = (
        "This sample message has code 12 and level INFO"
    )
    return fake_check


@pytest.fixture
def fake_checks(fake_check_warning, fake_check_error, fake_check_info):
    return [fake_check_warning, fake_check_error, fake_check_info]


def test_generate_rst_table(fake_checks):
    correct_rst_result = (
        ".. list-table:: Executed checks\n"
        + "   :widths: 10 20 40\n   :header-rows: 1\n\n"
        + "   * - Check number\n"
        + "     - Check level\n"
        + "     - Check message\n"
        + "   * - 0002\n"
        + "     - Warning\n"
        + "     - This sample message has code 2 and level WARNING\n"
        + "   * - 0012\n"
        + "     - Info\n"
        + "     - This sample message has code 12 and level INFO\n"
        + "   * - 1234\n"
        + "     - Error\n"
        + "     - This sample message has code 1234 and level ERROR"
    )
    rst_result = generate_rst_table(fake_checks)
    assert rst_result == correct_rst_result


def test_generate_csv_table(fake_checks):
    correct_csv_result = (
        '"error_code","level","description"\r\n'
        + '2,"WARNING","This sample message has code 2 and level WARNING"\r\n'
        + '12,"INFO","This sample message has code 12 and level INFO"\r\n'
        + '1234,"ERROR","This sample message has code 1234 and level ERROR"\r\n'
    )
    csv_result = generate_csv_table(fake_checks)
    assert csv_result == correct_csv_result


def test_export_with_geom(fake_check_error):
    fake_check_error.column.name = "foo"
    error_row_no_geom = MagicMock()
    error_row_no_geom.id = 1337
    error_row_no_geom.foo = "bar"
    del error_row_no_geom.geom
    error_row_geom = MagicMock()
    error_row_geom.geom = MagicMock(spec=WKBElement)
    result = export_with_geom(
        [(fake_check_error, error_row_no_geom), (fake_check_error, error_row_geom)]
    )
    # check all attributes for the first row
    assert result[0].name == fake_check_error.level.name
    assert result[0].code == fake_check_error.error_code
    assert result[0].id == 1337
    assert result[0].table == fake_check_error.table.name
    assert result[0].description == fake_check_error.description()
    assert result[0].column == "foo"
    assert result[0].value == "bar"
    assert result[0].geom is None
    # check geom for row with geom
    assert result[1].geom == error_row_geom.geom
