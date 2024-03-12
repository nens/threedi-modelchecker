import pytest
from threedi_schema import models

from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.checks.factories import (
    generate_enum_checks,
    generate_foreign_key_checks,
    generate_geometry_checks,
    generate_not_null_checks,
    generate_unique_checks,
)


def test_gen_foreign_key_checks():
    foreign_key_checks = generate_foreign_key_checks(models.Manhole.__table__)
    assert len(foreign_key_checks) == 1
    fk_check = foreign_key_checks[0]
    assert models.Manhole.connection_node_id == fk_check.column
    assert models.ConnectionNode.id == fk_check.reference_column


def test_gen_not_unique_checks():
    not_unique_checks = generate_unique_checks(models.Manhole.__table__)
    assert len(not_unique_checks) == 2
    assert models.Manhole.id == not_unique_checks[0].column
    assert models.Manhole.connection_node_id == not_unique_checks[1].column


def test_gen_not_null_checks():
    not_null_checks = generate_not_null_checks(models.Manhole.__table__)
    assert len(not_null_checks) == 3
    not_null_check_columns = [check.column for check in not_null_checks]
    assert models.Manhole.id in not_null_check_columns


def test_gen_geometry_check():
    geometry_checks = generate_geometry_checks(models.ConnectionNode.__table__)

    assert len(geometry_checks) == 1
    geometry_check_columns = [check.column for check in geometry_checks]
    assert models.ConnectionNode.the_geom in geometry_check_columns


def test_gen_enum_checks():
    enum_checks = generate_enum_checks(models.BoundaryConditions2D.__table__)

    assert len(enum_checks) == 1
    assert enum_checks[0].column == models.BoundaryConditions2D.boundary_type


def test_gen_enum_checks_varcharenum():
    enum_checks = generate_enum_checks(models.AggregationSettings.__table__)

    assert len(enum_checks) == 2
    enum_check_columns = [check.column for check in enum_checks]
    assert models.AggregationSettings.aggregation_method in enum_check_columns
    assert models.AggregationSettings.flow_variable in enum_check_columns


@pytest.mark.parametrize(
    "name", ["*.aggregation_method", "v2_aggregation_settings.aggregation_method"]
)
def test_gen_enum_checks_custom_mapping(name):
    enum_checks = generate_enum_checks(
        models.AggregationSettings.__table__,
        custom_level_map={name: "WARNING"},
    )

    assert len(enum_checks) == 2
    checks = {check.column.name: check for check in enum_checks}
    assert checks["aggregation_method"].level == CheckLevel.WARNING
    assert checks["flow_variable"].level == CheckLevel.ERROR
