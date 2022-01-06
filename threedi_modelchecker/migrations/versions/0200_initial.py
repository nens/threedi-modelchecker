"""Create all tables if they do not exist already.

Revision ID: 0200
Revises:
Create Date: 2021-02-15 16:31:00.792077

"""
from alembic import op
from sqlalchemy.engine.reflection import Inspector

import geoalchemy2
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0200"
down_revision = None
branch_labels = None
depends_on = None


existing_tables = []


def _get_existing_tables(inspector):
    """Fill the global 'existing_tables'"""
    global existing_tables

    existing_tables = inspector.get_table_names()


def create_table_if_not_exists(table_name, *args, **kwargs):
    """Create a table if it is not in the global 'existing_tables'"""
    if table_name in existing_tables:
        return
    else:
        existing_tables.append(table_name)
        return op.create_table(table_name, *args, **kwargs)


def _get_version(connection):
    if "south_migrationhistory" not in existing_tables:
        return
    res = connection.execute(
        "SELECT id FROM south_migrationhistory ORDER BY id DESC LIMIT 1"
    )
    results = res.fetchall()
    if len(results) == 1:
        return results[0][0]


def upgrade_160():
    """This implements a migration from the old stack:

    0160_auto__add_field_v2controlpid_target_upper_limit__add_field_v2controlpi

    Contents of forwards():

        # Adding field 'V2ControlPID.target_upper_limit'
        db.add_column(u'v2_control_pid', 'target_upper_limit',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2ControlPID.target_lower_limit'
        db.add_column(u'v2_control_pid', 'target_lower_limit',
                      self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True),
                      keep_default=False)
    """
    with op.batch_alter_table("v2_control_pid") as batch_op:
        batch_op.add_column(
            sa.Column("target_upper_limit", sa.String(length=50), nullable=True)
        )
        batch_op.add_column(
            sa.Column("target_lower_limit", sa.String(length=50), nullable=True)
        )


def upgrade_161():
    """This implements a migration from the old stack:

    0161_auto__del_field_v2globalsettings_connected_advise_file

    Contents of forwards():

        # Deleting field 'V2GlobalSettings.connected_advise_file'
        db.delete_column(u'v2_global_settings', 'connected_advise_file')

    """
    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.drop_column("connected_advise_file")


def upgrade_162():
    """This implements a migration from the old stack:

    0162_auto__add_field_v2globalsettings_table_step_size_1d__add_field_v2globa

    Contents of forwards():

        # Adding field 'V2GlobalSettings.table_step_size_1d'
        db.add_column(u'v2_global_settings', 'table_step_size_1d',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2GlobalSettings.table_step_size_volume_2d'
        db.add_column(u'v2_global_settings', 'table_step_size_volume_2d',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)

    """
    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.add_column(sa.Column("table_step_size_1d", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("table_step_size_volume_2d", sa.Float(), nullable=True)
        )


def upgrade_163():
    """This implements a migration from the old stack:

    0163_auto__add_field_v2globalsettings_use_2d_rain

    Contents of forwards():

        # Adding field 'V2GlobalSettings.use_2d_rain'
        db.add_column(u'v2_global_settings', 'use_2d_rain',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)

    """
    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.add_column(sa.Column("use_2d_rain", sa.Integer(), nullable=True))

    op.execute("UPDATE v2_global_settings SET use_2d_rain = 1")

    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.alter_column("use_2d_rain", nullable=False)


def upgrade_164():
    """This implements a migration from the old stack:

    0164_auto__add_v2gridrefinementarea

    Contents of forwards():

        # Adding model 'V2GridRefinementArea'
        if not db.dry_run:
            statement = get_srid_statement(db.db_alias)
            db_conn = DBConnector(db.db_alias)
            result = db_conn.free_form(statement, fetch=True)
            srid = result[0][0]

            db.create_table(u'v2_grid_refinement_area', (
                (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
                ('refinement_level', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
                ('code', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
                ('the_geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')(srid=srid, null=True, blank=True)),
            ))
            db.send_create_signal(u'threedi_tools', ['V2GridRefinementArea'])

    """
    create_table_if_not_exists(
        "v2_grid_refinement_area",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("refinement_level", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def upgrade_165():
    """This implements a migration from the old stack:

    0165_auto__add_v2groundwater__add_v2simpleinfiltration__add_v2interflow__ad

    Contents of forwards():

        # Adding model 'V2Groundwater'
        db.create_table(u'v2_groundwater', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('groundwater_impervious_layer_level', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('groundwater_impervious_layer_level_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('groundwater_impervious_layer_level_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('phreatic_storage_capacity', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('phreatic_storage_capacity_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('phreatic_storage_capacity_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('equilibrium_infiltration_rate', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('equilibrium_infiltration_rate_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('equilibrium_infiltration_rate_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('initial_infiltration_rate', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('initial_infiltration_rate_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('initial_infiltration_rate_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('infiltration_decay_period', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('infiltration_decay_period_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('infiltration_decay_period_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('groundwater_hydro_connectivity', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('groundwater_hydro_connectivity_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('groundwater_hydro_connectivity_type', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('seepage', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('seepage_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'threedi_tools', ['V2Groundwater'])

        # Adding model 'V2SimpleInfiltration'
        db.create_table(u'v2_simple_infiltration', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('infiltration_rate', self.gf('django.db.models.fields.FloatField')()),
            ('infiltration_rate_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('infiltration_surface_option', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('max_infiltration_capacity_file', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'threedi_tools', ['V2SimpleInfiltration'])

        # Adding model 'V2Interflow'
        db.create_table(u'v2_interflow', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('interflow_type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('porosity', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('porosity_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('porosity_layer_thickness', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('impervious_layer_elevation', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hydraulic_conductivity', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('hydraulic_conductivity_file', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'threedi_tools', ['V2Interflow'])

        # Adding field 'V2GlobalSettings.initial_groundwater_level'
        db.add_column(u'v2_global_settings', 'initial_groundwater_level',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2GlobalSettings.initial_groundwater_level_file'
        db.add_column(u'v2_global_settings', 'initial_groundwater_level_file',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2GlobalSettings.initial_groundwater_level_type'
        db.add_column(u'v2_global_settings', 'initial_groundwater_level_type',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2GlobalSettings.groundwater_settings'
        db.add_column(u'v2_global_settings', 'groundwater_settings',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['threedi_tools.V2Groundwater'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2GlobalSettings.simple_infiltration_settings'
        db.add_column(u'v2_global_settings', 'simple_infiltration_settings',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['threedi_tools.V2SimpleInfiltration'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2GlobalSettings.interflow_settings'
        db.add_column(u'v2_global_settings', 'interflow_settings',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['threedi_tools.V2Interflow'], null=True, blank=True),
                      keep_default=False)

    """
    create_table_if_not_exists(
        "v2_groundwater",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("groundwater_impervious_layer_level", sa.Float(), nullable=True),
        sa.Column(
            "groundwater_impervious_layer_level_file",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "groundwater_impervious_layer_level_type", sa.Integer(), nullable=True
        ),
        sa.Column("phreatic_storage_capacity", sa.Float(), nullable=True),
        sa.Column(
            "phreatic_storage_capacity_file", sa.String(length=255), nullable=True
        ),
        sa.Column("phreatic_storage_capacity_type", sa.Integer(), nullable=True),
        sa.Column("equilibrium_infiltration_rate", sa.Float(), nullable=True),
        sa.Column(
            "equilibrium_infiltration_rate_file", sa.String(length=255), nullable=True
        ),
        sa.Column("equilibrium_infiltration_rate_type", sa.Integer(), nullable=True),
        sa.Column("initial_infiltration_rate", sa.Float(), nullable=True),
        sa.Column(
            "initial_infiltration_rate_file", sa.String(length=255), nullable=True
        ),
        sa.Column("initial_infiltration_rate_type", sa.Integer(), nullable=True),
        sa.Column("infiltration_decay_period", sa.Float(), nullable=True),
        sa.Column(
            "infiltration_decay_period_file", sa.String(length=255), nullable=True
        ),
        sa.Column("infiltration_decay_period_type", sa.Integer(), nullable=True),
        sa.Column("groundwater_hydro_connectivity", sa.Float(), nullable=True),
        sa.Column(
            "groundwater_hydro_connectivity_file", sa.String(length=255), nullable=True
        ),
        sa.Column("groundwater_hydro_connectivity_type", sa.Integer(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("seepage", sa.Float(), nullable=True),
        sa.Column("seepage_file", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "v2_simple_infiltration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("infiltration_rate", sa.Float(), nullable=True),
        sa.Column("infiltration_rate_file", sa.String(length=255), nullable=True),
        sa.Column("infiltration_surface_option", sa.Integer(), nullable=True),
        sa.Column("max_infiltration_capacity_file", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    create_table_if_not_exists(
        "v2_interflow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interflow_type", sa.Integer(), nullable=False),
        sa.Column("porosity", sa.Float(), nullable=True),
        sa.Column("porosity_file", sa.String(length=255), nullable=True),
        sa.Column("porosity_layer_thickness", sa.Float(), nullable=True),
        sa.Column("impervious_layer_elevation", sa.Float(), nullable=True),
        sa.Column("hydraulic_conductivity", sa.Float(), nullable=True),
        sa.Column("hydraulic_conductivity_file", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.add_column(
            sa.Column("initial_groundwater_level", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "initial_groundwater_level_file", sa.String(length=255), nullable=True
            )
        )
        batch_op.add_column(
            sa.Column("initial_groundwater_level_type", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("groundwater_settings_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("simple_infiltration_settings_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("interflow_settings_id", sa.Integer(), nullable=True)
        )


def upgrade_166():
    """This implements a migration from the old stack:

    0166_fill_Groundwater_Interflow_SimpleInfiltration

    Contents of forwards():

        # Note: Don't use "from appname.models import ModelName".
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.

        # Get all rows in the globalsettings
        global_settings = orm.V2GlobalSettings.objects.all()
        for gs in global_settings:
            # create a new interflow entry
            interflow = orm.V2Interflow()
            interflow.interflow_type = gs.interflow_type
            interflow.porosity = gs.porosity
            interflow.porosity_file = gs.porosity_file
            interflow.porosity_layer_thickness = gs.porosity_layer_thickness
            interflow.impervious_layer_elevation = gs.impervious_layer_elevation
            interflow.hydraulic_conductivity = gs.hydraulic_conductivity
            interflow.hydraulic_conductivity_file = gs.hydraulic_conductivity_file
            interflow.save()
            # create a new simple_infiltration entry
            simple_infiltration = orm.V2SimpleInfiltration()
            simple_infiltration.infiltration_rate = gs.infiltration_rate
            simple_infiltration.infiltration_rate_file = gs.infiltration_rate_file
            simple_infiltration.infiltration_surface_option = gs.infiltration_surface_option
            simple_infiltration.max_infiltration_capacity_file = gs.max_infiltration_capacity_file
            simple_infiltration.save()
            # link the global_setting to the new tables
            gs.interflow_settings = interflow
            gs.simple_infiltration_settings = simple_infiltration
            gs.save()
    """
    op.execute(
        """
    INSERT INTO v2_interflow (id, interflow_type, porosity, porosity_file, porosity_layer_thickness,
                              impervious_layer_elevation, hydraulic_conductivity, hydraulic_conductivity_file)
    SELECT id, interflow_type, porosity, porosity_file, porosity_layer_thickness,
           impervious_layer_elevation, hydraulic_conductivity, hydraulic_conductivity_file
    FROM v2_global_settings;
    """
    )
    op.execute(
        """
    INSERT INTO v2_simple_infiltration (id, infiltration_rate, infiltration_rate_file,
                                        infiltration_surface_option, max_infiltration_capacity_file)
    SELECT id, infiltration_rate, infiltration_rate_file,
           infiltration_surface_option, max_infiltration_capacity_file
    FROM v2_global_settings;
    """
    )
    op.execute(
        """UPDATE v2_global_settings SET interflow_settings_id = id, simple_infiltration_settings_id = id"""
    )


def upgrade_167():
    """This implements a migration from the old stack:

    0167_auto__del_field_v2globalsettings_infiltration_rate_file__del_field_v2g

    Contents of forwards():

        # Deleting field 'V2GlobalSettings.infiltration_rate_file'
        db.delete_column(u'v2_global_settings', 'infiltration_rate_file')

        # Deleting field 'V2GlobalSettings.infiltration_surface_option'
        db.delete_column(u'v2_global_settings', 'infiltration_surface_option')

        # Deleting field 'V2GlobalSettings.max_infiltration_capacity_file'
        db.delete_column(u'v2_global_settings', 'max_infiltration_capacity_file')

        # Deleting field 'V2GlobalSettings.porosity_layer_thickness'
        db.delete_column(u'v2_global_settings', 'porosity_layer_thickness')

        # Deleting field 'V2GlobalSettings.porosity_file'
        db.delete_column(u'v2_global_settings', 'porosity_file')

        # Deleting field 'V2GlobalSettings.hydraulic_conductivity_file'
        db.delete_column(u'v2_global_settings', 'hydraulic_conductivity_file')

        # Deleting field 'V2GlobalSettings.interflow_type'
        db.delete_column(u'v2_global_settings', 'interflow_type')

        # Deleting field 'V2GlobalSettings.porosity'
        db.delete_column(u'v2_global_settings', 'porosity')

        # Deleting field 'V2GlobalSettings.impervious_layer_elevation'
        db.delete_column(u'v2_global_settings', 'impervious_layer_elevation')

        # Deleting field 'V2GlobalSettings.infiltration_rate'
        db.delete_column(u'v2_global_settings', 'infiltration_rate')

        # Deleting field 'V2GlobalSettings.hydraulic_conductivity'
        db.delete_column(u'v2_global_settings', 'hydraulic_conductivity')
    """
    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.drop_column("infiltration_rate_file")
        batch_op.drop_column("infiltration_surface_option")
        batch_op.drop_column("max_infiltration_capacity_file")
        batch_op.drop_column("porosity_layer_thickness")
        batch_op.drop_column("porosity_file")
        batch_op.drop_column("hydraulic_conductivity_file")
        batch_op.drop_column("interflow_type")
        batch_op.drop_column("porosity")
        batch_op.drop_column("impervious_layer_elevation")
        batch_op.drop_column("infiltration_rate")
        batch_op.drop_column("hydraulic_conductivity")


def upgrade_168():
    """This implements a migration from the old stack:

    0168_auto__del_field_v2groundwater_seepage_file__del_field_v2groundwater_se.py

    Contents of forwards():

        # Deleting field 'V2Groundwater.seepage_file'
        db.delete_column(u'v2_groundwater', 'seepage_file')

        # Deleting field 'V2Groundwater.seepage'
        db.delete_column(u'v2_groundwater', 'seepage')

        # Adding field 'V2Groundwater.leakage'
        db.add_column(u'v2_groundwater', 'leakage',
                      self.gf('django.db.models.fields.FloatField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'V2Groundwater.leakage_file'
        db.add_column(u'v2_groundwater', 'leakage_file',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Deleting field 'MduSettings.seepage_file'
        db.delete_column(u'settings', 'seepage_file')

        # Adding field 'MduSettings.leakage_file'
        db.add_column(u'settings', 'leakage_file',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)
    """
    # Ignored settings table migrations, this table will be removed anyway

    with op.batch_alter_table("v2_groundwater") as batch_op:
        batch_op.drop_column("seepage_file")
        batch_op.drop_column("seepage")
        batch_op.add_column(sa.Column("leakage", sa.Float(), nullable=True))
        batch_op.add_column(
            sa.Column("leakage_file", sa.String(length=255), nullable=True)
        )


def upgrade_169():
    """This implements a migration from the old stack:

    0169_auto__del_field_mdusettings_leakage_file__add_field_mdusettings_seepag.py

    Contents of forwards():

        # Deleting field 'MduSettings.leakage_file'
        db.delete_column(u'settings', 'leakage_file')

        # Adding field 'MduSettings.seepage_file'
        db.add_column(u'settings', 'seepage_file',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)
    """
    # Ignored settings table migrations, this table will be removed anyway


def upgrade_170():
    """This implements a migration from the old stack:

    0170_auto__chg_field_v2aggregationsettings_aggregation_method.py

    Contents of forwards():

        # Changing field 'V2AggregationSettings.aggregation_method'
        db.alter_column(u'v2_aggregation_settings', 'aggregation_method',
            self.gf('django.db.models.fields.CharField')(max_length=100))
    """
    with op.batch_alter_table("v2_aggregation_settings") as batch_op:
        batch_op.alter_column("aggregation_method", type_=sa.String(length=100))


def upgrade_171():
    """This implements a migration from the old stack:

    0170_auto__chg_field_v2culvert_discharge_coefficient_negative__chg_field_v2.py

    Contents of forwards():

        # We need to drop the view because it it not possible to alter a column
        # on a table with a view: https://www.postgresql.org/message-id/CAB7nPqTLmMn1LTb5WE0v0dO57iP0U73yKwzbZytAXDF1CAWLZg%40mail.gmail.com
        if not db.db_alias == 'spatialite':
            db.execute("DROP View IF EXISTS v2_culvert_view")

        # Changing field 'V2Culvert.discharge_coefficient_negative'
        db.alter_column(u'v2_culvert', 'discharge_coefficient_negative', self.gf('django.db.models.fields.FloatField')(default=1))

        # Changing field 'V2Culvert.discharge_coefficient_positive'
        db.alter_column(u'v2_culvert', 'discharge_coefficient_positive', self.gf('django.db.models.fields.FloatField')(default=1))

        # recreate the view
        if not db.db_alias == 'spatialite':
            view_statements = get_threedi_core_view_statements(
                flavor="postgresql")
            db.execute(view_statements['v2_culvert_view'])
    """
    op.execute(
        "UPDATE v2_culvert SET discharge_coefficient_negative = 1.0 WHERE discharge_coefficient_negative IS NULL"
    )
    op.execute(
        "UPDATE v2_culvert SET discharge_coefficient_positive = 1.0 WHERE discharge_coefficient_positive IS NULL"
    )

    with op.batch_alter_table("v2_culvert") as batch_op:
        batch_op.alter_column("discharge_coefficient_negative", nullable=False)
        batch_op.alter_column("discharge_coefficient_positive", nullable=False)


def upgrade_172():
    """This implements a migration from the old stack:

    0171_auto__chg_field_v2aggregationsettings_aggregation_method__del_field_v2.py

    Contents of forwards():

        db.rename_column(u'v2_global_settings', 'max_interception_file', 'interception_file')
        db.rename_column(u'v2_global_settings', 'max_interception', 'interception_global')
    """
    with op.batch_alter_table("v2_global_settings") as batch_op:
        batch_op.alter_column(
            "max_interception_file", new_column_name="interception_file"
        )
        batch_op.alter_column("max_interception", new_column_name="interception_global")


def upgrade_173():
    """This implements a migration from the old stack:

    0172_auto__del_v2initialwaterlevel__del_field_v2orifice_max_capacity__del_f

    Contents of forwards():

        # Deleting model 'V2InitialWaterlevel'
        db.delete_table(u'v2_initial_waterlevel')

        # Deleting field 'V2Orifice.max_capacity'
        db.delete_column(u'v2_orifice', 'max_capacity')

        # Deleting field 'V2ImperviousSurface.function'
        db.delete_column(u'v2_impervious_surface', 'function')

        # Deleting field 'V2Pipe.pipe_quality'
        db.delete_column(u'v2_pipe', 'pipe_quality')

        # We need to drop the view because it it not possible to alter a column
        # on a table with a view: https://www.postgresql.org/message-id/CAB7nPqTLmMn1LTb5WE0v0dO57iP0U73yKwzbZytAXDF1CAWLZg%40mail.gmail.com
        if not db.db_alias == 'spatialite':
            db.execute("DROP View IF EXISTS v2_culvert_view")

        # Changing field 'V2Culvert.discharge_coefficient_negative'
        db.alter_column(u'v2_culvert', 'discharge_coefficient_negative', self.gf('django.db.models.fields.FloatField')())

        # Changing field 'V2Culvert.discharge_coefficient_positive'
        db.alter_column(u'v2_culvert', 'discharge_coefficient_positive', self.gf('django.db.models.fields.FloatField')())

        # recreate the view
        if not db.db_alias == 'spatialite':
            view_statements = get_threedi_core_view_statements(
                flavor="postgresql")
            db.execute(view_statements['v2_culvert_view'])
    """
    op.drop_table("v2_initial_waterlevel")

    with op.batch_alter_table("v2_orifice") as batch_op:
        batch_op.drop_column("max_capacity")

    with op.batch_alter_table("v2_impervious_surface") as batch_op:
        batch_op.drop_column("function")

    with op.batch_alter_table("v2_pipe") as batch_op:
        batch_op.drop_column("pipe_quality")

    with op.batch_alter_table("v2_culvert") as batch_op:
        batch_op.alter_column("discharge_coefficient_negative", nullable=True)
        batch_op.alter_column("discharge_coefficient_positive", nullable=True)


UPGRADE_LOOKUP = {
    160: upgrade_160,
    161: upgrade_161,
    162: upgrade_162,
    163: upgrade_163,
    164: upgrade_164,
    165: upgrade_165,
    166: upgrade_166,
    167: upgrade_167,
    168: upgrade_168,
    169: upgrade_169,
    170: upgrade_170,
    171: upgrade_171,
    172: upgrade_172,
    173: upgrade_173,
}


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Setup the global 'existing_tables'
    _get_existing_tables(inspector)

    # Initialize the Spatialite if necessary:
    if conn.dialect.name == "sqlite" and "spatial_ref_sys" not in existing_tables:
        op.execute("SELECT InitSpatialMetadata()")

    version = _get_version(conn)
    if version is not None:
        for i in range(version, 174):
            UPGRADE_LOOKUP[i]()

    create_table_if_not_exists(
        "v2_2d_boundary_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("timeseries", sa.Text(), nullable=True),
        sa.Column("boundary_type", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_2d_lateral",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("timeseries", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_calculation_point",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_type_id", sa.Integer(), nullable=True),
        sa.Column("user_ref", sa.String(length=80), nullable=False),
        sa.Column("calc_type", sa.Integer(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_connection_nodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("storage_area", sa.Float(), nullable=True),
        sa.Column("initial_waterlevel", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "the_geom_linestring",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_delta",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("measure_delta", sa.String(length=50), nullable=True),
        sa.Column("measure_dt", sa.Float(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_value", sa.String(length=50), nullable=True),
        sa.Column("action_time", sa.Float(), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_measure_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_memory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("upper_threshold", sa.Float(), nullable=True),
        sa.Column("lower_threshold", sa.Float(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_value", sa.String(length=50), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_inverse", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_pid",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("setpoint", sa.Float(), nullable=True),
        sa.Column("kp", sa.Float(), nullable=True),
        sa.Column("ki", sa.Float(), nullable=True),
        sa.Column("kd", sa.Float(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_upper_limit", sa.String(length=50), nullable=True),
        sa.Column("target_lower_limit", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_table",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_table", sa.Text(), nullable=True),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("measure_variable", sa.String(length=50), nullable=True),
        sa.Column("measure_operator", sa.String(length=2), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_timed",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=True),
        sa.Column("action_table", sa.Text(), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_cross_section_definition",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("width", sa.String(length=255), nullable=True),
        sa.Column("height", sa.String(length=255), nullable=True),
        sa.Column("shape", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_dem_average_area",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_floodfill",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("waterlevel", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_grid_refinement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("refinement_level", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_grid_refinement_area",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("refinement_level", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_groundwater",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("groundwater_impervious_layer_level", sa.Float(), nullable=True),
        sa.Column(
            "groundwater_impervious_layer_level_file",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "groundwater_impervious_layer_level_type", sa.Integer(), nullable=True
        ),
        sa.Column("phreatic_storage_capacity", sa.Float(), nullable=True),
        sa.Column(
            "phreatic_storage_capacity_file", sa.String(length=255), nullable=True
        ),
        sa.Column("phreatic_storage_capacity_type", sa.Integer(), nullable=True),
        sa.Column("equilibrium_infiltration_rate", sa.Float(), nullable=True),
        sa.Column(
            "equilibrium_infiltration_rate_file", sa.String(length=255), nullable=True
        ),
        sa.Column("equilibrium_infiltration_rate_type", sa.Integer(), nullable=True),
        sa.Column("initial_infiltration_rate", sa.Float(), nullable=True),
        sa.Column(
            "initial_infiltration_rate_file", sa.String(length=255), nullable=True
        ),
        sa.Column("initial_infiltration_rate_type", sa.Integer(), nullable=True),
        sa.Column("infiltration_decay_period", sa.Float(), nullable=True),
        sa.Column(
            "infiltration_decay_period_file", sa.String(length=255), nullable=True
        ),
        sa.Column("infiltration_decay_period_type", sa.Integer(), nullable=True),
        sa.Column("groundwater_hydro_connectivity", sa.Float(), nullable=True),
        sa.Column(
            "groundwater_hydro_connectivity_file", sa.String(length=255), nullable=True
        ),
        sa.Column("groundwater_hydro_connectivity_type", sa.Integer(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("leakage", sa.Float(), nullable=True),
        sa.Column("leakage_file", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_impervious_surface",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("surface_inclination", sa.String(length=64), nullable=False),
        sa.Column("surface_class", sa.String(length=128), nullable=False),
        sa.Column("surface_sub_class", sa.String(length=128), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("nr_of_inhabitants", sa.Float(), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("dry_weather_flow", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_interflow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("interflow_type", sa.Integer(), nullable=False),
        sa.Column("porosity", sa.Float(), nullable=True),
        sa.Column("porosity_file", sa.String(length=255), nullable=True),
        sa.Column("porosity_layer_thickness", sa.Float(), nullable=True),
        sa.Column("impervious_layer_elevation", sa.Float(), nullable=True),
        sa.Column("hydraulic_conductivity", sa.Float(), nullable=True),
        sa.Column("hydraulic_conductivity_file", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_levee",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("crest_level", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("material", sa.Integer(), nullable=True),
        sa.Column("max_breach_depth", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_numerical_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cfl_strictness_factor_1d", sa.Float(), nullable=True),
        sa.Column("cfl_strictness_factor_2d", sa.Float(), nullable=True),
        sa.Column("convergence_cg", sa.Float(), nullable=True),
        sa.Column("convergence_eps", sa.Float(), nullable=True),
        sa.Column("flow_direction_threshold", sa.Float(), nullable=True),
        sa.Column("frict_shallow_water_correction", sa.Integer(), nullable=True),
        sa.Column("general_numerical_threshold", sa.Float(), nullable=True),
        sa.Column("integration_method", sa.Integer(), nullable=True),
        sa.Column("limiter_grad_1d", sa.Integer(), nullable=True),
        sa.Column("limiter_grad_2d", sa.Integer(), nullable=True),
        sa.Column("limiter_slope_crossectional_area_2d", sa.Integer(), nullable=True),
        sa.Column("limiter_slope_friction_2d", sa.Integer(), nullable=True),
        sa.Column("max_nonlin_iterations", sa.Integer(), nullable=True),
        sa.Column("max_degree", sa.Integer(), nullable=False),
        sa.Column("minimum_friction_velocity", sa.Float(), nullable=True),
        sa.Column("minimum_surface_area", sa.Float(), nullable=True),
        sa.Column("precon_cg", sa.Integer(), nullable=True),
        sa.Column("preissmann_slot", sa.Float(), nullable=True),
        sa.Column("pump_implicit_ratio", sa.Float(), nullable=True),
        sa.Column("thin_water_layer_definition", sa.Float(), nullable=True),
        sa.Column("use_of_cg", sa.Integer(), nullable=False),
        sa.Column("use_of_nested_newton", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_obstacle",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("crest_level", sa.Float(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_simple_infiltration",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("infiltration_rate", sa.Float(), nullable=True),
        sa.Column("infiltration_rate_file", sa.String(length=255), nullable=True),
        sa.Column("infiltration_surface_option", sa.Integer(), nullable=True),
        sa.Column("max_infiltration_capacity_file", sa.Text(), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_surface_parameters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("outflow_delay", sa.Float(), nullable=False),
        sa.Column("surface_layer_thickness", sa.Float(), nullable=False),
        sa.Column("infiltration", sa.Boolean(), nullable=False),
        sa.Column("max_infiltration_capacity", sa.Float(), nullable=False),
        sa.Column("min_infiltration_capacity", sa.Float(), nullable=False),
        sa.Column("infiltration_decay_constant", sa.Float(), nullable=False),
        sa.Column("infiltration_recovery_constant", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_1d_boundary_conditions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("boundary_type", sa.Integer(), nullable=False),
        sa.Column("timeseries", sa.Text(), nullable=True),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_node_id"),
    )
    create_table_if_not_exists(
        "v2_1d_lateral",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.Column("timeseries", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_channel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_connected_pnt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("calculation_pnt_id", sa.Integer(), nullable=False),
        sa.Column("levee_id", sa.Integer(), nullable=True),
        sa.Column("exchange_level", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("control_group_id", sa.Integer(), nullable=True),
        sa.Column("measure_group_id", sa.Integer(), nullable=True),
        sa.Column("control_type", sa.String(length=15), nullable=True),
        sa.Column("control_id", sa.Integer(), nullable=True),
        sa.Column("start", sa.String(length=50), nullable=True),
        sa.Column("end", sa.String(length=50), nullable=True),
        sa.Column("measure_frequency", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_control_measure_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("measure_group_id", sa.Integer(), nullable=True),
        sa.Column("object_type", sa.String(length=100), nullable=True),
        sa.Column("object_id", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_culvert",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=True),
        sa.Column("friction_value", sa.Float(), nullable=False),
        sa.Column("friction_type", sa.Integer(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("discharge_coefficient_positive", sa.Float(), nullable=True),
        sa.Column("discharge_coefficient_negative", sa.Float(), nullable=True),
        sa.Column("invert_level_start_point", sa.Float(), nullable=False),
        sa.Column("invert_level_end_point", sa.Float(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_global_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("use_2d_flow", sa.Boolean(), nullable=False),
        sa.Column("use_1d_flow", sa.Boolean(), nullable=False),
        sa.Column("manhole_storage_area", sa.Float(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("sim_time_step", sa.Float(), nullable=False),
        sa.Column("output_time_step", sa.Float(), nullable=True),
        sa.Column("nr_timesteps", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Text(), nullable=False),
        sa.Column("grid_space", sa.Float(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=False),
        sa.Column("kmax", sa.Integer(), nullable=False),
        sa.Column("guess_dams", sa.Integer(), nullable=True),
        sa.Column("table_step_size", sa.Float(), nullable=False),
        sa.Column("flooding_threshold", sa.Float(), nullable=False),
        sa.Column("advection_1d", sa.Integer(), nullable=False),
        sa.Column("advection_2d", sa.Integer(), nullable=False),
        sa.Column("dem_file", sa.String(length=255), nullable=True),
        sa.Column("frict_type", sa.Integer(), nullable=True),
        sa.Column("frict_coef", sa.Float(), nullable=False),
        sa.Column("frict_coef_file", sa.String(length=255), nullable=True),
        sa.Column("water_level_ini_type", sa.Integer(), nullable=True),
        sa.Column("initial_waterlevel", sa.Float(), nullable=False),
        sa.Column("initial_waterlevel_file", sa.String(length=255), nullable=True),
        sa.Column("interception_global", sa.Float(), nullable=True),
        sa.Column("interception_file", sa.String(length=255), nullable=True),
        sa.Column("dem_obstacle_detection", sa.Boolean(), nullable=False),
        sa.Column("dem_obstacle_height", sa.Float(), nullable=True),
        sa.Column("embedded_cutoff_threshold", sa.Float(), nullable=True),
        sa.Column("epsg_code", sa.Integer(), nullable=True),
        sa.Column("timestep_plus", sa.Boolean(), nullable=False),
        sa.Column("max_angle_1d_advection", sa.Float(), nullable=True),
        sa.Column("minimum_sim_time_step", sa.Float(), nullable=True),
        sa.Column("maximum_sim_time_step", sa.Float(), nullable=True),
        sa.Column("frict_avg", sa.Integer(), nullable=True),
        sa.Column("wind_shielding_file", sa.String(length=255), nullable=True),
        sa.Column("use_0d_inflow", sa.Integer(), nullable=True),
        sa.Column("table_step_size_1d", sa.Float(), nullable=True),
        sa.Column("table_step_size_volume_2d", sa.Float(), nullable=True),
        sa.Column("use_2d_rain", sa.Integer(), nullable=False),
        sa.Column("initial_groundwater_level", sa.Float(), nullable=True),
        sa.Column(
            "initial_groundwater_level_file", sa.String(length=255), nullable=True
        ),
        sa.Column("initial_groundwater_level_type", sa.Integer(), nullable=True),
        sa.Column("numerical_settings_id", sa.Integer(), nullable=False),
        sa.Column("interflow_settings_id", sa.Integer(), nullable=True),
        sa.Column("control_group_id", sa.Integer(), nullable=True),
        sa.Column("simple_infiltration_settings_id", sa.Integer(), nullable=True),
        sa.Column("groundwater_settings_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_impervious_surface_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=False),
        sa.Column("impervious_surface_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_manhole",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("shape", sa.String(length=4), nullable=True),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("length", sa.Float(), nullable=True),
        sa.Column("surface_level", sa.Float(), nullable=True),
        sa.Column("bottom_level", sa.Float(), nullable=False),
        sa.Column("drain_level", sa.Float(), nullable=True),
        sa.Column("sediment_level", sa.Float(), nullable=True),
        sa.Column("manhole_indicator", sa.Integer(), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=True),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_orifice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("crest_type", sa.Integer(), nullable=False),
        sa.Column("crest_level", sa.Float(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=True),
        sa.Column("friction_type", sa.Integer(), nullable=True),
        sa.Column("discharge_coefficient_positive", sa.Float(), nullable=True),
        sa.Column("discharge_coefficient_negative", sa.Float(), nullable=True),
        sa.Column("sewerage", sa.Boolean(), nullable=False),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_pipe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("profile_num", sa.Integer(), nullable=True),
        sa.Column("sewerage_type", sa.Integer(), nullable=True),
        sa.Column("calculation_type", sa.Integer(), nullable=False),
        sa.Column("invert_level_start_point", sa.Float(), nullable=False),
        sa.Column("invert_level_end_point", sa.Float(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=False),
        sa.Column("friction_type", sa.Integer(), nullable=False),
        sa.Column("dist_calc_points", sa.Float(), nullable=True),
        sa.Column("material", sa.Integer(), nullable=True),
        sa.Column("original_length", sa.Float(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_pumpstation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("classification", sa.Integer(), nullable=True),
        sa.Column("sewerage", sa.Boolean(), nullable=True),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("start_level", sa.Float(), nullable=False),
        sa.Column("lower_stop_level", sa.Float(), nullable=False),
        sa.Column("upper_stop_level", sa.Float(), nullable=True),
        sa.Column("capacity", sa.Float(), nullable=False),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_surface",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("nr_of_inhabitants", sa.Float(), nullable=True),
        sa.Column("dry_weather_flow", sa.Float(), nullable=True),
        sa.Column("function", sa.String(length=64), nullable=True),
        sa.Column("area", sa.Float(), nullable=True),
        sa.Column("surface_parameters_id", sa.Integer(), nullable=False),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_surface_map",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("surface_type", sa.String(length=40), nullable=False),
        sa.Column("surface_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_id", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_weir",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("crest_level", sa.Float(), nullable=False),
        sa.Column("crest_type", sa.Integer(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=True),
        sa.Column("friction_type", sa.Integer(), nullable=True),
        sa.Column("discharge_coefficient_positive", sa.Float(), nullable=True),
        sa.Column("discharge_coefficient_negative", sa.Float(), nullable=True),
        sa.Column("sewerage", sa.Boolean(), nullable=True),
        sa.Column("external", sa.Boolean(), nullable=True),
        sa.Column("zoom_category", sa.Integer(), nullable=True),
        sa.Column("connection_node_start_id", sa.Integer(), nullable=False),
        sa.Column("connection_node_end_id", sa.Integer(), nullable=False),
        sa.Column("cross_section_definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_aggregation_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("global_settings_id", sa.Integer(), nullable=True),
        sa.Column("var_name", sa.String(length=100), nullable=False),
        sa.Column("flow_variable", sa.String(length=100), nullable=False),
        sa.Column("aggregation_method", sa.String(length=100), nullable=True),
        sa.Column("aggregation_in_space", sa.Boolean(), nullable=False),
        sa.Column("timestep", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_cross_section_location",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=True),
        sa.Column("reference_level", sa.Float(), nullable=False),
        sa.Column("friction_type", sa.Integer(), nullable=False),
        sa.Column("friction_value", sa.Float(), nullable=False),
        sa.Column("bank_level", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=False,
        ),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("definition_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    create_table_if_not_exists(
        "v2_windshielding",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("north", sa.Float(), nullable=True),
        sa.Column("northeast", sa.Float(), nullable=True),
        sa.Column("east", sa.Float(), nullable=True),
        sa.Column("southeast", sa.Float(), nullable=True),
        sa.Column("south", sa.Float(), nullable=True),
        sa.Column("southwest", sa.Float(), nullable=True),
        sa.Column("west", sa.Float(), nullable=True),
        sa.Column("northwest", sa.Float(), nullable=True),
        sa.Column(
            "the_geom",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                management=True,
            ),
            nullable=True,
        ),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    pass
