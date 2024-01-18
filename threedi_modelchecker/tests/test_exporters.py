import pytest

from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.exporters import generate_csv_table, generate_rst_table


@pytest.fixture
def fake_checks():
    class FakeCheck:
        def __init__(self, level, error_code):
            self.level = level
            self.error_code = error_code

        def description(self):
            return f"This sample message has code {self.error_code} and level {self.level.name}"

    fake_checks = [
        FakeCheck(level=CheckLevel.WARNING, error_code=2),
        FakeCheck(level=CheckLevel.ERROR, error_code=1234),
        FakeCheck(level=CheckLevel.INFO, error_code=12),
    ]

    return fake_checks


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
