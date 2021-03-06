from threedi_modelchecker.checks.factories import generate_foreign_key_checks
from threedi_modelchecker.checks.factories import generate_unique_checks
from threedi_modelchecker.checks.factories import generate_not_null_checks
from threedi_modelchecker.checks.factories import generate_geometry_checks
from threedi_modelchecker.checks.factories import generate_enum_checks
from threedi_modelchecker.threedi_model import models


def test_gen_foreign_key_checks():
    foreign_key_checks = generate_foreign_key_checks(models.Manhole.__table__)
    assert len(foreign_key_checks) == 1
    fk_check = foreign_key_checks[0]
    assert models.Manhole.connection_node_id == fk_check.column
    assert models.ConnectionNode.id == fk_check.reference_column


def test_gen_not_unique_checks():
    not_unique_checks = generate_unique_checks(models.Manhole.__table__)
    assert len(not_unique_checks) == 1
    assert models.Manhole.id == not_unique_checks[0].column


def test_gen_not_null_checks():
    not_null_checks = generate_not_null_checks(models.Manhole.__table__)
    assert len(not_null_checks) == 5
    not_null_check_columns = [check.column for check in not_null_checks]
    assert models.Manhole.id in not_null_check_columns
    assert models.Manhole.code in not_null_check_columns
    assert models.Manhole.display_name in not_null_check_columns


def test_gen_geometry_check():
    geometry_checks = generate_geometry_checks(models.ConnectionNode.__table__)

    assert len(geometry_checks) == 2
    geometry_check_columns = [check.column for check in geometry_checks]
    assert models.ConnectionNode.the_geom in geometry_check_columns
    assert models.ConnectionNode.the_geom_linestring in geometry_check_columns


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
