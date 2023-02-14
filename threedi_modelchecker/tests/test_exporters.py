import pytest
from threedi_modelchecker.checks.base import CheckLevel

from threedi_modelchecker.exporters import (
    generate_rst_table, generate_csv_table
)

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
    correct_rst_result = (".. list-table:: Executed checks\n" +
                          "   :widths: 10 20 40\n   :header-rows: 1\n\n" +
                          "   * - Check number\n" +
                          "     - Check level\n" +
                          "     - Check message\n" +
                          "   * - 0002\n" +
                          "     - Warning\n" +
                          "     - This sample message has code 2 and level WARNING\n" +
                          "   * - 1234\n" +
                          "     - Error\n" +
                          "     - This sample message has code 1234 and level ERROR\n" +
                          "   * - 0012\n" +
                          "     - Info\n" +
                          "     - This sample message has code 12 and level INFO")
    rst_result = generate_rst_table(fake_checks)
    assert rst_result == correct_rst_result