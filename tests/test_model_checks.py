import pytest

from threedi_modelchecker.model_checks import ThreediModelChecker
from threedi_modelchecker.exporters import format_check_results
from tests.factories import MigrationHistoryFactory
from threedi_modelchecker.threedi_model import constants


@pytest.fixture
def model_checker(threedi_db):
    MigrationHistoryFactory(
        id=constants.LATEST_MIGRATION_ID,
        migration=constants.LATEST_MIGRATION_NAME,
    )
    return ThreediModelChecker(threedi_db)


def test_get_model_error_iterator(model_checker):
    for check, error in model_checker.errors():
        print(format_check_results(check, error))


def test_get_model_error_iterator_table_column(model_checker):
    for check, error in model_checker.errors('v2_weir', 'id'):
        print(format_check_results(check, error))


def test_get_model_checks_table(model_checker):
    v2_weir_checks = model_checker.checks('v2_weir')
    for c in v2_weir_checks:
        assert c.table.name == 'v2_weir'


def test_get_model_checks_table_column(model_checker):
    v2_weir_id_checks = model_checker.checks('v2_weir', 'id')
    for c in v2_weir_id_checks:
        assert c.table.name == 'v2_weir'
        assert c.column.name == 'id'


def test_get_model_checks_is_subset(model_checker):
    v2_weir_checks = model_checker.checks('v2_weir')
    v2_weir_checks_count = 0
    for _ in v2_weir_checks:
        v2_weir_checks_count += 1
    v2_weir_id_checks = model_checker.checks('v2_weir', 'id')
    v2_weir_id_checks_count = 0
    for _ in v2_weir_id_checks:
        v2_weir_id_checks_count += 1
    assert v2_weir_checks_count > v2_weir_id_checks_count
