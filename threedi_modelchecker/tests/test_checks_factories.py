import pytest
from threedi_schema import models

from threedi_modelchecker.checks.base import CheckLevel
from threedi_modelchecker.checks.factories import (
    ForeignKeyCheckSetting,
    generate_enum_checks,
    generate_epsg_geom_checks,
    generate_epsg_raster_checks,
    generate_foreign_key_checks,
    generate_geometry_checks,
    generate_not_null_checks,
    generate_unique_checks,
)


def test_gen_foreign_key_checks_no_filter():
    settings = [
        ForeignKeyCheckSetting(
            models.Surface.surface_parameters_id, models.SurfaceParameters.id
        ),
        ForeignKeyCheckSetting(
            models.MemoryControl.target_id,
            models.Channel.id,
            models.MemoryControl.target_type == "channel",
        ),
    ]
    foreign_key_checks = generate_foreign_key_checks(
        models.Surface.__table__, fk_settings=settings
    )
    assert len(foreign_key_checks) == 1
    fk_check = foreign_key_checks[0]
    assert models.Surface.surface_parameters_id == fk_check.column
    assert models.SurfaceParameters.id == fk_check.reference_column


def test_gen_foreign_key_checks_filter():
    settings = [
        ForeignKeyCheckSetting(
            models.Surface.surface_parameters_id, models.SurfaceParameters.id
        ),
        ForeignKeyCheckSetting(
            models.MemoryControl.target_id,
            models.Channel.id,
            models.MemoryControl.target_type == "channel",
        ),
    ]
    foreign_key_checks = generate_foreign_key_checks(
        models.MemoryControl.__table__, fk_settings=settings
    )
    assert len(foreign_key_checks) == 1
    fk_check = foreign_key_checks[0]
    assert settings[1].filter == fk_check.filters


def test_gen_not_unique_checks():
    not_unique_checks = generate_unique_checks(models.Channel.__table__)
    assert len(not_unique_checks) == 1
    assert models.Channel.id == not_unique_checks[0].column


@pytest.mark.parametrize(
    "extra_columns", [None, [], [models.Channel.connection_node_id_end]]
)
def test_gen_not_null_checks(extra_columns):
    not_null_checks = generate_not_null_checks(
        models.Channel.__table__, extra_not_null_columns=extra_columns
    )
    if extra_columns is None:
        extra_columns = []
    assert len(not_null_checks) == 2 + len(extra_columns)
    not_null_check_columns = [check.column for check in not_null_checks]
    assert models.Channel.id in not_null_check_columns
    assert models.Channel.geom in not_null_check_columns
    for col in extra_columns:
        assert col in not_null_check_columns
    assert models.Channel.code not in not_null_check_columns


def test_gen_geometry_check():
    geometry_checks = generate_geometry_checks(models.ConnectionNode.__table__)

    assert len(geometry_checks) == 1
    geometry_check_columns = [check.column for check in geometry_checks]
    assert models.ConnectionNode.geom in geometry_check_columns


def test_gen_enum_checks():
    enum_checks = generate_enum_checks(models.BoundaryConditions2D.__table__)

    assert len(enum_checks) == 1
    assert enum_checks[0].column == models.BoundaryConditions2D.type


def test_gen_enum_checks_varcharenum():
    enum_checks = generate_enum_checks(models.AggregationSettings.__table__)

    assert len(enum_checks) == 2
    enum_check_columns = [check.column for check in enum_checks]
    assert models.AggregationSettings.aggregation_method in enum_check_columns
    assert models.AggregationSettings.flow_variable in enum_check_columns


@pytest.mark.parametrize(
    "name", ["*.aggregation_method", "aggregation_settings.aggregation_method"]
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


@pytest.mark.parametrize(
    "model, nof_checks_expected",
    [
        (models.ModelSettings, 0),
        (models.ConnectionNode, 1),
    ],
)
def test_gen_epsg_geom_checks(model, nof_checks_expected):
    assert len(generate_epsg_geom_checks(model.__table__)) == nof_checks_expected


@pytest.mark.parametrize(
    "model, nof_checks_expected",
    [
        (models.ConnectionNode, 0),
        (models.GroundWater, 1),
        (models.ModelSettings, 2),
    ],
)
def test_gen_epsg_raster_checks(model, nof_checks_expected):
    raster_columns = [
        models.ModelSettings.dem_file,
        models.ModelSettings.friction_coefficient_file,
        models.GroundWater.equilibrium_infiltration_rate_file,
    ]
    assert (
        len(generate_epsg_raster_checks(model.__table__, raster_columns))
        == nof_checks_expected
    )
