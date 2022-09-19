--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: tiger; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA tiger;


--
-- Name: tiger_data; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA tiger_data;


--
-- Name: topology; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA topology;


--
-- Name: SCHEMA topology; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA topology IS 'PostGIS Topology schema';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: fuzzystrmatch; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch WITH SCHEMA public;


--
-- Name: EXTENSION fuzzystrmatch; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION fuzzystrmatch IS 'determine similarities and distance between strings';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry, geography, and raster spatial types and functions';


--
-- Name: postgis_tiger_geocoder; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder WITH SCHEMA tiger;


--
-- Name: EXTENSION postgis_tiger_geocoder; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis_tiger_geocoder IS 'PostGIS tiger geocoder and reverse geocoder';


--
-- Name: postgis_topology; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;


--
-- Name: EXTENSION postgis_topology; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis_topology IS 'PostGIS topology spatial types and functions';


--
-- Name: v2_1d_boundary_conditions; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_1d_boundary_conditions (
    id integer NOT NULL,
    connection_node_id integer NOT NULL,
    boundary_type integer,
    timeseries text
);


--
-- Name: v2_1d_boundary_conditions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_1d_boundary_conditions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_1d_boundary_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_1d_boundary_conditions_id_seq OWNED BY public.v2_1d_boundary_conditions.id;


--
-- Name: v2_1d_lateral; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_1d_lateral (
    id integer NOT NULL,
    connection_node_id integer NOT NULL,
    timeseries text
);


--
-- Name: v2_1d_lateral_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_1d_lateral_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_1d_lateral_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_1d_lateral_id_seq OWNED BY public.v2_1d_lateral.id;


--
-- Name: v2_2d_boundary_conditions; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_2d_boundary_conditions (
    id integer NOT NULL,
    display_name character varying(255),
    timeseries text,
    boundary_type integer,
    the_geom public.geometry(LineString,4326)
);


--
-- Name: v2_2d_boundary_conditions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_2d_boundary_conditions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_2d_boundary_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_2d_boundary_conditions_id_seq OWNED BY public.v2_2d_boundary_conditions.id;


--
-- Name: v2_2d_lateral; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_2d_lateral (
    id integer NOT NULL,
    type integer,
    the_geom public.geometry(Point,4326),
    timeseries text
);


--
-- Name: v2_2d_lateral_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_2d_lateral_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_2d_lateral_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_2d_lateral_id_seq OWNED BY public.v2_2d_lateral.id;


--
-- Name: v2_aggregation_settings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_aggregation_settings (
    id integer NOT NULL,
    global_settings_id integer,
    var_name character varying(100) NOT NULL,
    flow_variable character varying(100),
    aggregation_method character varying(100) NOT NULL,
    timestep integer NOT NULL
);


--
-- Name: v2_aggregation_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_aggregation_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_aggregation_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_aggregation_settings_id_seq OWNED BY public.v2_aggregation_settings.id;


--
-- Name: v2_calculation_point; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_calculation_point (
    id integer NOT NULL,
    content_type_id integer,
    user_ref character varying(80) NOT NULL,
    calc_type integer,
    the_geom public.geometry(Point,4326) NOT NULL
);


--
-- Name: v2_calculation_point_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_calculation_point_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_calculation_point_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_calculation_point_id_seq OWNED BY public.v2_calculation_point.id;


--
-- Name: v2_channel; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_channel (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    calculation_type integer,
    dist_calc_points double precision,
    zoom_category integer,
    the_geom public.geometry(LineString,4326) NOT NULL,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- Name: v2_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_channel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_channel_id_seq OWNED BY public.v2_channel.id;


--
-- Name: v2_connected_pnt; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_connected_pnt (
    id integer NOT NULL,
    exchange_level double precision,
    calculation_pnt_id integer NOT NULL,
    levee_id integer,
    the_geom public.geometry(Point,4326) NOT NULL
);


--
-- Name: v2_connected_pnt_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_connected_pnt_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_connected_pnt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_connected_pnt_id_seq OWNED BY public.v2_connected_pnt.id;


--
-- Name: v2_connection_nodes; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_connection_nodes (
    id integer NOT NULL,
    storage_area double precision,
    initial_waterlevel double precision,
    the_geom public.geometry(Point,4326) NOT NULL,
    the_geom_linestring public.geometry(LineString,4326),
    code character varying(100)
);


--
-- Name: v2_connection_nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_connection_nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_connection_nodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_connection_nodes_id_seq OWNED BY public.v2_connection_nodes.id;


--
-- Name: v2_control; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control (
    id integer NOT NULL,
    control_group_id integer,
    control_type character varying(15),
    control_id integer,
    measure_group_id integer,
    start character varying(50),
    "end" character varying(50),
    measure_frequency integer
);


--
-- Name: v2_control_delta; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_delta (
    id integer NOT NULL,
    measure_variable character varying(50),
    measure_delta double precision,
    measure_dt double precision,
    action_type character varying(50),
    action_value character varying(50),
    action_time double precision,
    target_type character varying(100),
    target_id integer
);


--
-- Name: v2_control_delta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_delta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_delta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_delta_id_seq OWNED BY public.v2_control_delta.id;


--
-- Name: v2_control_group; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_group (
    id integer NOT NULL,
    name character varying(100),
    description text
);


--
-- Name: v2_control_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_group_id_seq OWNED BY public.v2_control_group.id;


--
-- Name: v2_control_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_id_seq OWNED BY public.v2_control.id;


--
-- Name: v2_control_measure_group; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_measure_group (
    id integer NOT NULL
);


--
-- Name: v2_control_measure_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_measure_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_measure_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_measure_group_id_seq OWNED BY public.v2_control_measure_group.id;


--
-- Name: v2_control_measure_map; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_measure_map (
    id integer NOT NULL,
    measure_group_id integer,
    object_type character varying(100),
    object_id integer,
    weight numeric(3,2)
);


--
-- Name: v2_control_measure_map_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_measure_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_measure_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_measure_map_id_seq OWNED BY public.v2_control_measure_map.id;


--
-- Name: v2_control_memory; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_memory (
    id integer NOT NULL,
    measure_variable character varying(50),
    upper_threshold double precision,
    lower_threshold double precision,
    action_type character varying(50),
    action_value character varying(50),
    target_type character varying(100),
    target_id integer,
    is_active boolean NOT NULL,
    is_inverse boolean NOT NULL
);


--
-- Name: v2_control_memory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_memory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_memory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_memory_id_seq OWNED BY public.v2_control_memory.id;


--
-- Name: v2_control_pid; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_pid (
    id integer NOT NULL,
    measure_variable character varying(50),
    setpoint double precision,
    kp double precision,
    ki double precision,
    kd double precision,
    action_type character varying(50),
    target_type character varying(100),
    target_id integer,
    target_upper_limit character varying(50),
    target_lower_limit character varying(50)
);


--
-- Name: v2_control_pid_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_pid_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_pid_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_pid_id_seq OWNED BY public.v2_control_pid.id;


--
-- Name: v2_control_table; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_table (
    id integer NOT NULL,
    action_table text,
    action_type character varying(50),
    measure_variable character varying(50),
    measure_operator character varying(2),
    target_type character varying(100),
    target_id integer
);


--
-- Name: v2_control_table_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_table_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_table_id_seq OWNED BY public.v2_control_table.id;


--
-- Name: v2_control_timed; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_control_timed (
    id integer NOT NULL,
    action_type character varying(50),
    action_table text,
    target_type character varying(100),
    target_id integer
);


--
-- Name: v2_control_timed_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_control_timed_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_control_timed_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_control_timed_id_seq OWNED BY public.v2_control_timed.id;


--
-- Name: v2_cross_section_definition; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_cross_section_definition (
    id integer NOT NULL,
    shape integer,
    width character varying(255),
    height character varying(255),
    code character varying(100)
);


--
-- Name: v2_cross_section_definition_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_cross_section_definition_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_cross_section_definition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_cross_section_definition_id_seq OWNED BY public.v2_cross_section_definition.id;


--
-- Name: v2_cross_section_location; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_cross_section_location (
    id integer NOT NULL,
    channel_id integer,
    definition_id integer NOT NULL,
    reference_level double precision,
    friction_type integer,
    friction_value double precision,
    bank_level double precision,
    the_geom public.geometry(Point,4326) NOT NULL,
    code character varying(100)
);


--
-- Name: v2_cross_section_location_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_cross_section_location_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_cross_section_location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_cross_section_location_id_seq OWNED BY public.v2_cross_section_location.id;


--
-- Name: v2_cross_section_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_cross_section_view AS
 SELECT def.id AS def_id,
    def.shape AS def_shape,
    def.width AS def_width,
    def.height AS def_height,
    def.code AS def_code,
    l.id AS l_id,
    l.channel_id AS l_channel_id,
    l.definition_id AS l_definition_id,
    l.reference_level AS l_reference_level,
    l.friction_type AS l_friction_type,
    l.friction_value AS l_friction_value,
    l.bank_level AS l_bank_level,
    l.code AS l_code,
    l.the_geom,
    ch.id AS ch_id,
    ch.display_name AS ch_display_name,
    ch.code AS ch_code,
    ch.calculation_type AS ch_calculation_type,
    ch.dist_calc_points AS ch_dist_calc_points,
    ch.zoom_category AS ch_zoom_category,
    ch.connection_node_start_id AS ch_connection_node_start_id,
    ch.connection_node_end_id AS ch_connection_node_end_id
   FROM public.v2_cross_section_definition def,
    public.v2_cross_section_location l,
    public.v2_channel ch
  WHERE ((l.definition_id = def.id) AND (l.channel_id = ch.id));


--
-- Name: v2_culvert; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_culvert (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    calculation_type integer,
    friction_value double precision,
    friction_type integer,
    dist_calc_points double precision,
    zoom_category integer,
    cross_section_definition_id integer,
    discharge_coefficient_positive double precision NOT NULL,
    discharge_coefficient_negative double precision NOT NULL,
    invert_level_start_point double precision,
    invert_level_end_point double precision,
    the_geom public.geometry(LineString,4326) NOT NULL,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- Name: v2_culvert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_culvert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_culvert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_culvert_id_seq OWNED BY public.v2_culvert.id;


--
-- Name: v2_culvert_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_culvert_view AS
 SELECT cul.id AS cul_id,
    cul.display_name AS cul_display_name,
    cul.code AS cul_code,
    cul.calculation_type AS cul_calculation_type,
    cul.friction_value AS cul_friction_value,
    cul.friction_type AS cul_friction_type,
    cul.dist_calc_points AS cul_dist_calc_points,
    cul.zoom_category AS cul_zoom_category,
    cul.cross_section_definition_id AS cul_cross_section_definition_id,
    cul.discharge_coefficient_positive AS cul_discharge_coefficient_positive,
    cul.discharge_coefficient_negative AS cul_discharge_coefficient_negative,
    cul.invert_level_start_point AS cul_invert_level_start_point,
    cul.invert_level_end_point AS cul_invert_level_end_point,
    cul.the_geom,
    cul.connection_node_start_id AS cul_connection_node_start_id,
    cul.connection_node_end_id AS cul_connection_node_end_id,
    def.id AS def_id,
    def.shape AS def_shape,
    def.width AS def_width,
    def.height AS def_height,
    def.code AS def_code
   FROM public.v2_culvert cul,
    public.v2_cross_section_definition def
  WHERE (cul.cross_section_definition_id = def.id);


--
-- Name: v2_dem_average_area; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_dem_average_area (
    id integer NOT NULL,
    the_geom public.geometry(Polygon,4326)
);


--
-- Name: v2_dem_average_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_dem_average_area_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_dem_average_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_dem_average_area_id_seq OWNED BY public.v2_dem_average_area.id;


--
-- Name: v2_floodfill; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_floodfill (
    id integer NOT NULL,
    waterlevel double precision,
    the_geom public.geometry(Point,4326)
);


--
-- Name: v2_floodfill_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_floodfill_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_floodfill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_floodfill_id_seq OWNED BY public.v2_floodfill.id;


--
-- Name: v2_global_settings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_global_settings (
    id integer NOT NULL,
    use_2d_flow boolean NOT NULL,
    use_1d_flow boolean NOT NULL,
    manhole_storage_area double precision,
    name character varying(128),
    sim_time_step double precision NOT NULL,
    output_time_step double precision,
    nr_timesteps integer NOT NULL,
    start_time timestamp with time zone,
    start_date date NOT NULL,
    grid_space double precision NOT NULL,
    dist_calc_points double precision NOT NULL,
    kmax integer NOT NULL,
    guess_dams integer,
    minimum_table_step_size double precision NOT NULL,
    maximum_table_step_size double precision,
    flooding_threshold double precision NOT NULL,
    advection_1d integer NOT NULL,
    advection_2d integer NOT NULL,
    dem_file character varying(255),
    frict_type integer,
    frict_coef double precision NOT NULL,
    frict_coef_file character varying(255),
    water_level_ini_type integer,
    initial_waterlevel double precision NOT NULL,
    initial_waterlevel_file character varying(255),
    interception_global double precision,
    interception_file character varying(255),
    dem_obstacle_detection boolean NOT NULL,
    dem_obstacle_height double precision,
    embedded_cutoff_threshold double precision,
    epsg_code integer,
    timestep_plus boolean NOT NULL,
    max_angle_1d_advection double precision,
    minimum_sim_time_step double precision,
    maximum_sim_time_step double precision,
    frict_avg integer NOT NULL,
    wind_shielding_file character varying(255),
    control_group_id integer,
    numerical_settings_id integer NOT NULL,
    use_0d_inflow integer NOT NULL,
    table_step_size_1d double precision,
    use_2d_rain integer NOT NULL,
    initial_groundwater_level double precision,
    initial_groundwater_level_file character varying(255),
    initial_groundwater_level_type integer,
    groundwater_settings_id integer,
    simple_infiltration_settings_id integer,
    interflow_settings_id integer
);


--
-- Name: v2_global_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_global_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_global_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_global_settings_id_seq OWNED BY public.v2_global_settings.id;


--
-- Name: v2_grid_refinement; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_grid_refinement (
    id integer NOT NULL,
    display_name character varying(255),
    refinement_level integer NOT NULL,
    the_geom public.geometry(LineString,4326) NOT NULL,
    code character varying(100)
);


--
-- Name: v2_grid_refinement_area; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_grid_refinement_area (
    id integer NOT NULL,
    display_name character varying(255),
    refinement_level integer NOT NULL,
    code character varying(100),
    the_geom public.geometry(Polygon,4326) NOT NULL
);


--
-- Name: v2_grid_refinement_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_grid_refinement_area_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_grid_refinement_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_grid_refinement_area_id_seq OWNED BY public.v2_grid_refinement_area.id;


--
-- Name: v2_grid_refinement_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_grid_refinement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_grid_refinement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_grid_refinement_id_seq OWNED BY public.v2_grid_refinement.id;


--
-- Name: v2_groundwater; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_groundwater (
    id integer NOT NULL,
    groundwater_impervious_layer_level double precision,
    groundwater_impervious_layer_level_file character varying(255),
    groundwater_impervious_layer_level_type integer,
    phreatic_storage_capacity double precision,
    phreatic_storage_capacity_file character varying(255),
    phreatic_storage_capacity_type integer,
    equilibrium_infiltration_rate double precision,
    equilibrium_infiltration_rate_file character varying(255),
    equilibrium_infiltration_rate_type integer,
    initial_infiltration_rate double precision,
    initial_infiltration_rate_file character varying(255),
    initial_infiltration_rate_type integer,
    infiltration_decay_period double precision,
    infiltration_decay_period_file character varying(255),
    infiltration_decay_period_type integer,
    groundwater_hydro_connectivity double precision,
    groundwater_hydro_connectivity_file character varying(255),
    groundwater_hydro_connectivity_type integer,
    display_name character varying(255),
    leakage double precision,
    leakage_file character varying(255)
);


--
-- Name: v2_groundwater_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_groundwater_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_groundwater_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_groundwater_id_seq OWNED BY public.v2_groundwater.id;


--
-- Name: v2_impervious_surface; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_impervious_surface (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    surface_class character varying(128) NOT NULL,
    surface_sub_class character varying(128),
    surface_inclination character varying(64) NOT NULL,
    zoom_category integer,
    nr_of_inhabitants double precision,
    dry_weather_flow double precision,
    area double precision,
    the_geom public.geometry(Polygon,4326)
);


--
-- Name: v2_impervious_surface_map; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_impervious_surface_map (
    id integer NOT NULL,
    impervious_surface_id integer,
    connection_node_id integer NOT NULL,
    percentage double precision
);


--
-- Name: v2_imp_surface_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_imp_surface_view AS
 SELECT isurfmap.id AS isurfmap_id,
    isurfmap.impervious_surface_id AS isurfmap_impervious_surface_id,
    isurfmap.connection_node_id AS isurfmap_connection_node_id,
    isurfmap.percentage AS isurfmap_percentage,
    public.st_makeline(public.st_centroid(isurf.the_geom), connection_node.the_geom) AS the_geom
   FROM public.v2_impervious_surface isurf,
    public.v2_connection_nodes connection_node,
    public.v2_impervious_surface_map isurfmap
  WHERE ((isurfmap.connection_node_id = connection_node.id) AND (isurfmap.impervious_surface_id = isurf.id));


--
-- Name: v2_impervious_surface_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_impervious_surface_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_impervious_surface_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_impervious_surface_id_seq OWNED BY public.v2_impervious_surface.id;


--
-- Name: v2_impervious_surface_map_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_impervious_surface_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_impervious_surface_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_impervious_surface_map_id_seq OWNED BY public.v2_impervious_surface_map.id;


--
-- Name: v2_interflow; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_interflow (
    id integer NOT NULL,
    interflow_type integer NOT NULL,
    porosity double precision,
    porosity_file character varying(255),
    porosity_layer_thickness double precision,
    impervious_layer_elevation double precision,
    hydraulic_conductivity double precision,
    hydraulic_conductivity_file character varying(255),
    display_name character varying(255)
);


--
-- Name: v2_interflow_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_interflow_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_interflow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_interflow_id_seq OWNED BY public.v2_interflow.id;


--
-- Name: v2_levee; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_levee (
    id integer NOT NULL,
    crest_level double precision,
    the_geom public.geometry(LineString,4326),
    material integer,
    max_breach_depth double precision,
    code character varying(100)
);


--
-- Name: v2_levee_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_levee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_levee_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_levee_id_seq OWNED BY public.v2_levee.id;


--
-- Name: v2_manhole; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_manhole (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    connection_node_id integer NOT NULL,
    shape character varying(4),
    width double precision,
    length double precision,
    manhole_indicator integer,
    calculation_type integer,
    bottom_level double precision,
    surface_level double precision,
    drain_level double precision,
    sediment_level double precision,
    zoom_category integer
);


--
-- Name: v2_manhole_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_manhole_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_manhole_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_manhole_id_seq OWNED BY public.v2_manhole.id;


--
-- Name: v2_manhole_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_manhole_view AS
 SELECT manh.id AS manh_id,
    manh.display_name AS manh_display_name,
    manh.code AS manh_code,
    manh.connection_node_id AS manh_connection_node_id,
    manh.shape AS manh_shape,
    manh.width AS manh_width,
    manh.length AS manh_length,
    manh.manhole_indicator AS manh_manhole_indicator,
    manh.calculation_type AS manh_calculation_type,
    manh.bottom_level AS manh_bottom_level,
    manh.surface_level AS manh_surface_level,
    manh.drain_level AS manh_drain_level,
    manh.sediment_level AS manh_sediment_level,
    manh.zoom_category AS manh_zoom_category,
    node.id AS node_id,
    node.storage_area AS node_storage_area,
    node.initial_waterlevel AS node_initial_waterlevel,
    node.code AS node_code,
    node.the_geom,
    node.the_geom_linestring AS node_the_geom_linestring
   FROM public.v2_manhole manh,
    public.v2_connection_nodes node
  WHERE (manh.connection_node_id = node.id);


--
-- Name: v2_numerical_settings; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_numerical_settings (
    id integer NOT NULL,
    cfl_strictness_factor_1d double precision,
    cfl_strictness_factor_2d double precision,
    convergence_cg double precision,
    convergence_eps double precision,
    flow_direction_threshold double precision,
    frict_shallow_water_correction integer,
    general_numerical_threshold double precision,
    integration_method integer,
    limiter_grad_1d integer,
    limiter_grad_2d integer,
    limiter_slope_crossectional_area_2d integer,
    limiter_slope_friction_2d integer,
    max_nonlin_iterations integer,
    max_degree integer NOT NULL,
    minimum_friction_velocity double precision,
    minimum_surface_area double precision,
    precon_cg integer,
    preissmann_slot double precision,
    pump_implicit_ratio double precision,
    thin_water_layer_definition double precision,
    use_of_cg integer NOT NULL,
    use_of_nested_newton integer NOT NULL
);


--
-- Name: v2_numerical_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_numerical_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_numerical_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_numerical_settings_id_seq OWNED BY public.v2_numerical_settings.id;


--
-- Name: v2_obstacle; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_obstacle (
    id integer NOT NULL,
    crest_level double precision,
    the_geom public.geometry(LineString,4326),
    code character varying(100)
);


--
-- Name: v2_obstacle_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_obstacle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_obstacle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_obstacle_id_seq OWNED BY public.v2_obstacle.id;


--
-- Name: v2_orifice; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_orifice (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    crest_level double precision,
    sewerage boolean,
    cross_section_definition_id integer,
    friction_value double precision,
    friction_type integer,
    discharge_coefficient_positive double precision,
    discharge_coefficient_negative double precision,
    zoom_category integer,
    crest_type integer,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- Name: v2_orifice_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_orifice_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_orifice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_orifice_id_seq OWNED BY public.v2_orifice.id;


--
-- Name: v2_orifice_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_orifice_view AS
 SELECT orf.id AS orf_id,
    orf.display_name AS orf_display_name,
    orf.code AS orf_code,
    orf.crest_level AS orf_crest_level,
    orf.sewerage AS orf_sewerage,
    orf.cross_section_definition_id AS orf_cross_section_definition_id,
    orf.friction_value AS orf_friction_value,
    orf.friction_type AS orf_friction_type,
    orf.discharge_coefficient_positive AS orf_discharge_coefficient_positive,
    orf.discharge_coefficient_negative AS orf_discharge_coefficient_negative,
    orf.zoom_category AS orf_zoom_category,
    orf.crest_type AS orf_crest_type,
    orf.connection_node_start_id AS orf_connection_node_start_id,
    orf.connection_node_end_id AS orf_connection_node_end_id,
    def.id AS def_id,
    def.shape AS def_shape,
    def.width AS def_width,
    def.height AS def_height,
    def.code AS def_code,
    public.st_makeline(start_node.the_geom, end_node.the_geom) AS the_geom
   FROM public.v2_orifice orf,
    public.v2_cross_section_definition def,
    public.v2_connection_nodes start_node,
    public.v2_connection_nodes end_node
  WHERE (((orf.connection_node_start_id = start_node.id) AND (orf.connection_node_end_id = end_node.id)) AND (orf.cross_section_definition_id = def.id));


--
-- Name: v2_pipe; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_pipe (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    profile_num integer,
    sewerage_type integer,
    calculation_type integer,
    invert_level_start_point double precision,
    invert_level_end_point double precision,
    cross_section_definition_id integer,
    friction_value double precision,
    friction_type integer,
    dist_calc_points double precision,
    material integer,
    original_length double precision,
    zoom_category integer,
    connection_node_start_id integer NOT NULL,
    connection_node_end_id integer NOT NULL
);


--
-- Name: v2_pipe_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_pipe_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_pipe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_pipe_id_seq OWNED BY public.v2_pipe.id;


--
-- Name: v2_pipe_map_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_pipe_map_view AS
 SELECT DISTINCT ON (isurfmap.impervious_surface_id) isurf.id AS isurf_id,
    isurf.display_name AS isurf_display_name,
    isurf.code AS isurf_code,
    isurf.surface_class AS isurf_surface_class,
    isurf.surface_sub_class AS isurf_surface_sub_class,
    isurf.surface_inclination AS isurf_surface_inclination,
    isurf.zoom_category AS isurf_zoom_category,
    isurf.nr_of_inhabitants AS isurf_nr_of_inhabitants,
    isurf.dry_weather_flow AS isurf_dry_weather_flow,
    isurf.area AS isurf_area,
    public.st_makeline(public.st_centroid(isurf.the_geom), connection_node.the_geom) AS the_geom
   FROM public.v2_impervious_surface isurf,
    public.v2_connection_nodes connection_node,
    public.v2_impervious_surface_map isurfmap,
    public.v2_pipe p
  WHERE (((isurfmap.connection_node_id = connection_node.id) AND (isurfmap.impervious_surface_id = isurf.id)) AND ((isurfmap.connection_node_id = p.connection_node_start_id) OR (isurfmap.connection_node_id = p.connection_node_end_id)))
  ORDER BY isurfmap.impervious_surface_id, public.st_distance(connection_node.the_geom, isurf.the_geom);


--
-- Name: v2_pipe_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_pipe_view AS
 SELECT pipe.id AS pipe_id,
    pipe.display_name AS pipe_display_name,
    pipe.code AS pipe_code,
    pipe.profile_num AS pipe_profile_num,
    pipe.sewerage_type AS pipe_sewerage_type,
    pipe.calculation_type AS pipe_calculation_type,
    pipe.invert_level_start_point AS pipe_invert_level_start_point,
    pipe.invert_level_end_point AS pipe_invert_level_end_point,
    pipe.cross_section_definition_id AS pipe_cross_section_definition_id,
    pipe.friction_value AS pipe_friction_value,
    pipe.friction_type AS pipe_friction_type,
    pipe.dist_calc_points AS pipe_dist_calc_points,
    pipe.material AS pipe_material,
    pipe.original_length AS pipe_original_length,
    pipe.zoom_category AS pipe_zoom_category,
    pipe.connection_node_start_id AS pipe_connection_node_start_id,
    pipe.connection_node_end_id AS pipe_connection_node_end_id,
    def.id AS def_id,
    def.shape AS def_shape,
    def.width AS def_width,
    def.height AS def_height,
    def.code AS def_code,
    public.st_makeline(start_node.the_geom, end_node.the_geom) AS the_geom
   FROM public.v2_pipe pipe,
    public.v2_cross_section_definition def,
    public.v2_connection_nodes start_node,
    public.v2_connection_nodes end_node
  WHERE (((pipe.connection_node_start_id = start_node.id) AND (pipe.connection_node_end_id = end_node.id)) AND (pipe.cross_section_definition_id = def.id));


--
-- Name: v2_pumpstation; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_pumpstation (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    classification integer,
    sewerage boolean,
    start_level double precision,
    lower_stop_level double precision,
    upper_stop_level double precision,
    capacity double precision,
    zoom_category integer,
    connection_node_start_id integer,
    connection_node_end_id integer,
    type integer
);


--
-- Name: v2_pumpstation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_pumpstation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_pumpstation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_pumpstation_id_seq OWNED BY public.v2_pumpstation.id;


--
-- Name: v2_pumpstation_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_pumpstation_view AS
 SELECT pump.id AS pump_id,
    pump.display_name AS pump_display_name,
    pump.code AS pump_code,
    pump.classification AS pump_classification,
    pump.type AS pump_type,
    pump.sewerage AS pump_sewerage,
    pump.start_level AS pump_start_level,
    pump.lower_stop_level AS pump_lower_stop_level,
    pump.upper_stop_level AS pump_upper_stop_level,
    pump.capacity AS pump_capacity,
    pump.zoom_category AS pump_zoom_category,
    pump.connection_node_start_id AS pump_connection_node_start_id,
    pump.connection_node_end_id AS pump_connection_node_end_id,
    public.st_makeline(start_node.the_geom, end_node.the_geom) AS the_geom
   FROM public.v2_pumpstation pump,
    public.v2_connection_nodes start_node,
    public.v2_connection_nodes end_node
  WHERE ((pump.connection_node_start_id = start_node.id) AND (pump.connection_node_end_id = end_node.id));


--
-- Name: v2_simple_infiltration; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_simple_infiltration (
    id integer NOT NULL,
    infiltration_rate double precision NOT NULL,
    infiltration_rate_file character varying(255),
    infiltration_surface_option integer,
    max_infiltration_capacity_file text,
    display_name character varying(255)
);


--
-- Name: v2_simple_infiltration_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_simple_infiltration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_simple_infiltration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_simple_infiltration_id_seq OWNED BY public.v2_simple_infiltration.id;


--
-- Name: v2_surface; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_surface (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    zoom_category integer,
    nr_of_inhabitants double precision,
    dry_weather_flow double precision,
    function character varying(64),
    area double precision,
    surface_parameters_id integer,
    the_geom public.geometry(Polygon,4326)
);


--
-- Name: v2_surface_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_surface_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_surface_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_surface_id_seq OWNED BY public.v2_surface.id;


--
-- Name: v2_surface_map; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_surface_map (
    id integer NOT NULL,
    surface_type character varying(40),
    surface_id integer,
    connection_node_id integer NOT NULL,
    percentage double precision
);


--
-- Name: v2_surface_map_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_surface_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_surface_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_surface_map_id_seq OWNED BY public.v2_surface_map.id;


--
-- Name: v2_surface_parameters; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_surface_parameters (
    id integer NOT NULL,
    outflow_delay double precision NOT NULL,
    surface_layer_thickness double precision NOT NULL,
    infiltration boolean NOT NULL,
    max_infiltration_capacity double precision NOT NULL,
    min_infiltration_capacity double precision NOT NULL,
    infiltration_decay_constant double precision NOT NULL,
    infiltration_recovery_constant double precision NOT NULL
);


--
-- Name: v2_surface_parameters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_surface_parameters_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_surface_parameters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_surface_parameters_id_seq OWNED BY public.v2_surface_parameters.id;


--
-- Name: v2_weir; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_weir (
    id integer NOT NULL,
    display_name character varying(255),
    code character varying(100),
    crest_level double precision,
    crest_type integer,
    cross_section_definition_id integer,
    sewerage boolean,
    discharge_coefficient_positive double precision,
    discharge_coefficient_negative double precision,
    external boolean,
    zoom_category integer,
    friction_value double precision,
    friction_type integer,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- Name: v2_weir_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_weir_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_weir_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_weir_id_seq OWNED BY public.v2_weir.id;


--
-- Name: v2_weir_view; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v2_weir_view AS
 SELECT weir.id AS weir_id,
    weir.display_name AS weir_display_name,
    weir.code AS weir_code,
    weir.crest_level AS weir_crest_level,
    weir.crest_type AS weir_crest_type,
    weir.cross_section_definition_id AS weir_cross_section_definition_id,
    weir.sewerage AS weir_sewerage,
    weir.discharge_coefficient_positive AS weir_discharge_coefficient_positive,
    weir.discharge_coefficient_negative AS weir_discharge_coefficient_negative,
    weir.external AS weir_external,
    weir.zoom_category AS weir_zoom_category,
    weir.friction_value AS weir_friction_value,
    weir.friction_type AS weir_friction_type,
    weir.connection_node_start_id AS weir_connection_node_start_id,
    weir.connection_node_end_id AS weir_connection_node_end_id,
    def.id AS def_id,
    def.shape AS def_shape,
    def.width AS def_width,
    def.height AS def_height,
    def.code AS def_code,
    public.st_makeline(start_node.the_geom, end_node.the_geom) AS the_geom
   FROM public.v2_weir weir,
    public.v2_cross_section_definition def,
    public.v2_connection_nodes start_node,
    public.v2_connection_nodes end_node
  WHERE (((weir.connection_node_start_id = start_node.id) AND (weir.connection_node_end_id = end_node.id)) AND (weir.cross_section_definition_id = def.id));


--
-- Name: v2_windshielding; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE public.v2_windshielding (
    id integer NOT NULL,
    channel_id integer,
    north double precision,
    northeast double precision,
    east double precision,
    southeast double precision,
    south double precision,
    southwest double precision,
    west double precision,
    northwest double precision,
    the_geom public.geometry(Point,4326)
);


--
-- Name: v2_windshielding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.v2_windshielding_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: v2_windshielding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.v2_windshielding_id_seq OWNED BY public.v2_windshielding.id;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_1d_boundary_conditions ALTER COLUMN id SET DEFAULT nextval('public.v2_1d_boundary_conditions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_1d_lateral ALTER COLUMN id SET DEFAULT nextval('public.v2_1d_lateral_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_2d_boundary_conditions ALTER COLUMN id SET DEFAULT nextval('public.v2_2d_boundary_conditions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_2d_lateral ALTER COLUMN id SET DEFAULT nextval('public.v2_2d_lateral_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_aggregation_settings ALTER COLUMN id SET DEFAULT nextval('public.v2_aggregation_settings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_calculation_point ALTER COLUMN id SET DEFAULT nextval('public.v2_calculation_point_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_channel ALTER COLUMN id SET DEFAULT nextval('public.v2_channel_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_connected_pnt ALTER COLUMN id SET DEFAULT nextval('public.v2_connected_pnt_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_connection_nodes ALTER COLUMN id SET DEFAULT nextval('public.v2_connection_nodes_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control ALTER COLUMN id SET DEFAULT nextval('public.v2_control_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_delta ALTER COLUMN id SET DEFAULT nextval('public.v2_control_delta_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_group ALTER COLUMN id SET DEFAULT nextval('public.v2_control_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_measure_group ALTER COLUMN id SET DEFAULT nextval('public.v2_control_measure_group_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_measure_map ALTER COLUMN id SET DEFAULT nextval('public.v2_control_measure_map_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_memory ALTER COLUMN id SET DEFAULT nextval('public.v2_control_memory_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_pid ALTER COLUMN id SET DEFAULT nextval('public.v2_control_pid_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_table ALTER COLUMN id SET DEFAULT nextval('public.v2_control_table_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_timed ALTER COLUMN id SET DEFAULT nextval('public.v2_control_timed_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_cross_section_definition ALTER COLUMN id SET DEFAULT nextval('public.v2_cross_section_definition_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_cross_section_location ALTER COLUMN id SET DEFAULT nextval('public.v2_cross_section_location_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_culvert ALTER COLUMN id SET DEFAULT nextval('public.v2_culvert_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_dem_average_area ALTER COLUMN id SET DEFAULT nextval('public.v2_dem_average_area_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_floodfill ALTER COLUMN id SET DEFAULT nextval('public.v2_floodfill_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_global_settings ALTER COLUMN id SET DEFAULT nextval('public.v2_global_settings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_grid_refinement ALTER COLUMN id SET DEFAULT nextval('public.v2_grid_refinement_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_grid_refinement_area ALTER COLUMN id SET DEFAULT nextval('public.v2_grid_refinement_area_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_groundwater ALTER COLUMN id SET DEFAULT nextval('public.v2_groundwater_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_impervious_surface ALTER COLUMN id SET DEFAULT nextval('public.v2_impervious_surface_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_impervious_surface_map ALTER COLUMN id SET DEFAULT nextval('public.v2_impervious_surface_map_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_interflow ALTER COLUMN id SET DEFAULT nextval('public.v2_interflow_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_levee ALTER COLUMN id SET DEFAULT nextval('public.v2_levee_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_manhole ALTER COLUMN id SET DEFAULT nextval('public.v2_manhole_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_numerical_settings ALTER COLUMN id SET DEFAULT nextval('public.v2_numerical_settings_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_obstacle ALTER COLUMN id SET DEFAULT nextval('public.v2_obstacle_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_orifice ALTER COLUMN id SET DEFAULT nextval('public.v2_orifice_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pipe ALTER COLUMN id SET DEFAULT nextval('public.v2_pipe_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pumpstation ALTER COLUMN id SET DEFAULT nextval('public.v2_pumpstation_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_simple_infiltration ALTER COLUMN id SET DEFAULT nextval('public.v2_simple_infiltration_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_surface ALTER COLUMN id SET DEFAULT nextval('public.v2_surface_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_surface_map ALTER COLUMN id SET DEFAULT nextval('public.v2_surface_map_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_surface_parameters ALTER COLUMN id SET DEFAULT nextval('public.v2_surface_parameters_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_weir ALTER COLUMN id SET DEFAULT nextval('public.v2_weir_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_windshielding ALTER COLUMN id SET DEFAULT nextval('public.v2_windshielding_id_seq'::regclass);


--
-- Name: unique_connection_node; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_1d_boundary_conditions
    ADD CONSTRAINT unique_connection_node UNIQUE (connection_node_id);


--
-- Name: v2_1d_boundary_conditions_connection_node_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_1d_boundary_conditions
    ADD CONSTRAINT v2_1d_boundary_conditions_connection_node_id_key UNIQUE (connection_node_id);


--
-- Name: v2_1d_boundary_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_1d_boundary_conditions
    ADD CONSTRAINT v2_1d_boundary_conditions_pkey PRIMARY KEY (id);


--
-- Name: v2_1d_lateral_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_1d_lateral
    ADD CONSTRAINT v2_1d_lateral_pkey PRIMARY KEY (id);


--
-- Name: v2_2d_boundary_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_2d_boundary_conditions
    ADD CONSTRAINT v2_2d_boundary_conditions_pkey PRIMARY KEY (id);


--
-- Name: v2_2d_lateral_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_2d_lateral
    ADD CONSTRAINT v2_2d_lateral_pkey PRIMARY KEY (id);


--
-- Name: v2_aggregation_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_aggregation_settings
    ADD CONSTRAINT v2_aggregation_settings_pkey PRIMARY KEY (id);


--
-- Name: v2_calculation_point_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_calculation_point
    ADD CONSTRAINT v2_calculation_point_pkey PRIMARY KEY (id);


--
-- Name: v2_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_channel
    ADD CONSTRAINT v2_channel_pkey PRIMARY KEY (id);


--
-- Name: v2_connected_pnt_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_connected_pnt
    ADD CONSTRAINT v2_connected_pnt_pkey PRIMARY KEY (id);


--
-- Name: v2_connection_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_connection_nodes
    ADD CONSTRAINT v2_connection_nodes_pkey PRIMARY KEY (id);


--
-- Name: v2_control_delta_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_delta
    ADD CONSTRAINT v2_control_delta_pkey PRIMARY KEY (id);


--
-- Name: v2_control_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_group
    ADD CONSTRAINT v2_control_group_pkey PRIMARY KEY (id);


--
-- Name: v2_control_measure_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_measure_group
    ADD CONSTRAINT v2_control_measure_group_pkey PRIMARY KEY (id);


--
-- Name: v2_control_measure_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_measure_map
    ADD CONSTRAINT v2_control_measure_map_pkey PRIMARY KEY (id);


--
-- Name: v2_control_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_memory
    ADD CONSTRAINT v2_control_memory_pkey PRIMARY KEY (id);


--
-- Name: v2_control_pid_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_pid
    ADD CONSTRAINT v2_control_pid_pkey PRIMARY KEY (id);


--
-- Name: v2_control_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control
    ADD CONSTRAINT v2_control_pkey PRIMARY KEY (id);


--
-- Name: v2_control_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_table
    ADD CONSTRAINT v2_control_table_pkey PRIMARY KEY (id);


--
-- Name: v2_control_timed_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_control_timed
    ADD CONSTRAINT v2_control_timed_pkey PRIMARY KEY (id);


--
-- Name: v2_cross_section_definition_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_cross_section_definition
    ADD CONSTRAINT v2_cross_section_definition_pkey PRIMARY KEY (id);


--
-- Name: v2_cross_section_location_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_cross_section_location
    ADD CONSTRAINT v2_cross_section_location_pkey PRIMARY KEY (id);


--
-- Name: v2_culvert_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_culvert
    ADD CONSTRAINT v2_culvert_pkey PRIMARY KEY (id);


--
-- Name: v2_dem_average_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_dem_average_area
    ADD CONSTRAINT v2_dem_average_area_pkey PRIMARY KEY (id);


--
-- Name: v2_floodfill_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_floodfill
    ADD CONSTRAINT v2_floodfill_pkey PRIMARY KEY (id);


--
-- Name: v2_global_settings_name_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT v2_global_settings_name_uniq UNIQUE (name);


--
-- Name: v2_global_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT v2_global_settings_pkey PRIMARY KEY (id);


--
-- Name: v2_grid_refinement_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_grid_refinement_area
    ADD CONSTRAINT v2_grid_refinement_area_pkey PRIMARY KEY (id);


--
-- Name: v2_grid_refinement_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_grid_refinement
    ADD CONSTRAINT v2_grid_refinement_pkey PRIMARY KEY (id);


--
-- Name: v2_groundwater_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_groundwater
    ADD CONSTRAINT v2_groundwater_pkey PRIMARY KEY (id);


--
-- Name: v2_impervious_surface_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_impervious_surface_map
    ADD CONSTRAINT v2_impervious_surface_map_pkey PRIMARY KEY (id);


--
-- Name: v2_impervious_surface_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_impervious_surface
    ADD CONSTRAINT v2_impervious_surface_pkey PRIMARY KEY (id);


--
-- Name: v2_interflow_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_interflow
    ADD CONSTRAINT v2_interflow_pkey PRIMARY KEY (id);


--
-- Name: v2_levee_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_levee
    ADD CONSTRAINT v2_levee_pkey PRIMARY KEY (id);


--
-- Name: v2_manhole_connection_node_id_uniq; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_manhole
    ADD CONSTRAINT v2_manhole_connection_node_id_uniq UNIQUE (connection_node_id);


--
-- Name: v2_manhole_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_manhole
    ADD CONSTRAINT v2_manhole_pkey PRIMARY KEY (id);


--
-- Name: v2_numerical_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_numerical_settings
    ADD CONSTRAINT v2_numerical_settings_pkey PRIMARY KEY (id);


--
-- Name: v2_obstacle_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_obstacle
    ADD CONSTRAINT v2_obstacle_pkey PRIMARY KEY (id);


--
-- Name: v2_orifice_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_orifice
    ADD CONSTRAINT v2_orifice_pkey PRIMARY KEY (id);


--
-- Name: v2_pipe_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_pipe
    ADD CONSTRAINT v2_pipe_pkey PRIMARY KEY (id);


--
-- Name: v2_pumpstation_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_pumpstation
    ADD CONSTRAINT v2_pumpstation_pkey PRIMARY KEY (id);


--
-- Name: v2_simple_infiltration_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_simple_infiltration
    ADD CONSTRAINT v2_simple_infiltration_pkey PRIMARY KEY (id);


--
-- Name: v2_surface_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_surface_map
    ADD CONSTRAINT v2_surface_map_pkey PRIMARY KEY (id);


--
-- Name: v2_surface_parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_surface_parameters
    ADD CONSTRAINT v2_surface_parameters_pkey PRIMARY KEY (id);


--
-- Name: v2_surface_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_surface
    ADD CONSTRAINT v2_surface_pkey PRIMARY KEY (id);


--
-- Name: v2_weir_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_weir
    ADD CONSTRAINT v2_weir_pkey PRIMARY KEY (id);


--
-- Name: v2_windshielding_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY public.v2_windshielding
    ADD CONSTRAINT v2_windshielding_pkey PRIMARY KEY (id);

--
-- Name: v2_1d_lateral_connection_node_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_1d_lateral_connection_node_id ON public.v2_1d_lateral USING btree (connection_node_id);


--
-- Name: v2_2d_boundary_conditions_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_2d_boundary_conditions_the_geom_id ON public.v2_2d_boundary_conditions USING gist (the_geom);


--
-- Name: v2_2d_lateral_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_2d_lateral_the_geom_id ON public.v2_2d_lateral USING gist (the_geom);


--
-- Name: v2_aggregation_settings_global_settings_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_aggregation_settings_global_settings_id ON public.v2_aggregation_settings USING btree (global_settings_id);


--
-- Name: v2_calculation_point_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_calculation_point_the_geom_id ON public.v2_calculation_point USING gist (the_geom);


--
-- Name: v2_channel_connection_node_end_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_channel_connection_node_end_id ON public.v2_channel USING btree (connection_node_end_id);


--
-- Name: v2_channel_connection_node_start_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_channel_connection_node_start_id ON public.v2_channel USING btree (connection_node_start_id);


--
-- Name: v2_channel_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_channel_the_geom_id ON public.v2_channel USING gist (the_geom);


--
-- Name: v2_connected_pnt_calculation_pnt_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_connected_pnt_calculation_pnt_id ON public.v2_connected_pnt USING btree (calculation_pnt_id);


--
-- Name: v2_connected_pnt_levee_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_connected_pnt_levee_id ON public.v2_connected_pnt USING btree (levee_id);


--
-- Name: v2_connected_pnt_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_connected_pnt_the_geom_id ON public.v2_connected_pnt USING gist (the_geom);


--
-- Name: v2_connection_nodes_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_connection_nodes_the_geom_id ON public.v2_connection_nodes USING gist (the_geom);


--
-- Name: v2_connection_nodes_the_geom_linestring_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_connection_nodes_the_geom_linestring_id ON public.v2_connection_nodes USING gist (the_geom_linestring);


--
-- Name: v2_control_control_group_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_control_control_group_id ON public.v2_control USING btree (control_group_id);


--
-- Name: v2_control_measure_group_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_control_measure_group_id ON public.v2_control USING btree (measure_group_id);


--
-- Name: v2_control_measure_map_measure_group_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_control_measure_map_measure_group_id ON public.v2_control_measure_map USING btree (measure_group_id);


--
-- Name: v2_cross_section_location_channel_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_cross_section_location_channel_id ON public.v2_cross_section_location USING btree (channel_id);


--
-- Name: v2_cross_section_location_definition_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_cross_section_location_definition_id ON public.v2_cross_section_location USING btree (definition_id);


--
-- Name: v2_cross_section_location_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_cross_section_location_the_geom_id ON public.v2_cross_section_location USING gist (the_geom);


--
-- Name: v2_culvert_connection_node_end_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_culvert_connection_node_end_id ON public.v2_culvert USING btree (connection_node_end_id);


--
-- Name: v2_culvert_connection_node_start_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_culvert_connection_node_start_id ON public.v2_culvert USING btree (connection_node_start_id);


--
-- Name: v2_culvert_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_culvert_cross_section_definition_id ON public.v2_culvert USING btree (cross_section_definition_id);


--
-- Name: v2_culvert_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_culvert_the_geom_id ON public.v2_culvert USING gist (the_geom);


--
-- Name: v2_dem_average_area_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_dem_average_area_the_geom_id ON public.v2_dem_average_area USING gist (the_geom);


--
-- Name: v2_floodfill_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_floodfill_the_geom_id ON public.v2_floodfill USING gist (the_geom);


--
-- Name: v2_global_settings_control_group_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_global_settings_control_group_id ON public.v2_global_settings USING btree (control_group_id);


--
-- Name: v2_global_settings_groundwater_settings_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_global_settings_groundwater_settings_id ON public.v2_global_settings USING btree (groundwater_settings_id);


--
-- Name: v2_global_settings_interflow_settings_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_global_settings_interflow_settings_id ON public.v2_global_settings USING btree (interflow_settings_id);


--
-- Name: v2_global_settings_numerical_settings_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_global_settings_numerical_settings_id ON public.v2_global_settings USING btree (numerical_settings_id);


--
-- Name: v2_global_settings_simple_infiltration_settings_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_global_settings_simple_infiltration_settings_id ON public.v2_global_settings USING btree (simple_infiltration_settings_id);


--
-- Name: v2_grid_refinement_area_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_grid_refinement_area_the_geom_id ON public.v2_grid_refinement_area USING gist (the_geom);


--
-- Name: v2_grid_refinement_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_grid_refinement_the_geom_id ON public.v2_grid_refinement USING gist (the_geom);


--
-- Name: v2_impervious_surface_map_connection_node_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_impervious_surface_map_connection_node_id ON public.v2_impervious_surface_map USING btree (connection_node_id);


--
-- Name: v2_impervious_surface_map_impervious_surface_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_impervious_surface_map_impervious_surface_id ON public.v2_impervious_surface_map USING btree (impervious_surface_id);


--
-- Name: v2_impervious_surface_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_impervious_surface_the_geom_id ON public.v2_impervious_surface USING gist (the_geom);


--
-- Name: v2_levee_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_levee_the_geom_id ON public.v2_levee USING gist (the_geom);


--
-- Name: v2_manhole_connection_node_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_manhole_connection_node_id ON public.v2_manhole USING btree (connection_node_id);


--
-- Name: v2_obstacle_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_obstacle_the_geom_id ON public.v2_obstacle USING gist (the_geom);


--
-- Name: v2_orifice_connection_node_end_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_orifice_connection_node_end_id ON public.v2_orifice USING btree (connection_node_end_id);


--
-- Name: v2_orifice_connection_node_start_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_orifice_connection_node_start_id ON public.v2_orifice USING btree (connection_node_start_id);


--
-- Name: v2_orifice_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_orifice_cross_section_definition_id ON public.v2_orifice USING btree (cross_section_definition_id);


--
-- Name: v2_pipe_connection_node_end_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_pipe_connection_node_end_id ON public.v2_pipe USING btree (connection_node_end_id);


--
-- Name: v2_pipe_connection_node_start_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_pipe_connection_node_start_id ON public.v2_pipe USING btree (connection_node_start_id);


--
-- Name: v2_pipe_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_pipe_cross_section_definition_id ON public.v2_pipe USING btree (cross_section_definition_id);


--
-- Name: v2_pumpstation_connection_node_end_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_pumpstation_connection_node_end_id ON public.v2_pumpstation USING btree (connection_node_end_id);


--
-- Name: v2_pumpstation_connection_node_start_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_pumpstation_connection_node_start_id ON public.v2_pumpstation USING btree (connection_node_start_id);


--
-- Name: v2_surface_map_connection_node_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_surface_map_connection_node_id ON public.v2_surface_map USING btree (connection_node_id);


--
-- Name: v2_surface_surface_parameters_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_surface_surface_parameters_id ON public.v2_surface USING btree (surface_parameters_id);


--
-- Name: v2_surface_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_surface_the_geom_id ON public.v2_surface USING gist (the_geom);


--
-- Name: v2_weir_connection_node_end_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_weir_connection_node_end_id ON public.v2_weir USING btree (connection_node_end_id);


--
-- Name: v2_weir_connection_node_start_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_weir_connection_node_start_id ON public.v2_weir USING btree (connection_node_start_id);


--
-- Name: v2_weir_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_weir_cross_section_definition_id ON public.v2_weir USING btree (cross_section_definition_id);


--
-- Name: v2_windshielding_channel_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_windshielding_channel_id ON public.v2_windshielding USING btree (channel_id);


--
-- Name: v2_windshielding_the_geom_id; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX v2_windshielding_the_geom_id ON public.v2_windshielding USING gist (the_geom);



--
-- Name: calculation_pnt_id_refs_id_3a23ca39; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_connected_pnt
    ADD CONSTRAINT calculation_pnt_id_refs_id_3a23ca39 FOREIGN KEY (calculation_pnt_id) REFERENCES public.v2_calculation_point(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: channel_id_refs_id_0941f88e; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_cross_section_location
    ADD CONSTRAINT channel_id_refs_id_0941f88e FOREIGN KEY (channel_id) REFERENCES public.v2_channel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: channel_id_refs_id_79d66cdb; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_windshielding
    ADD CONSTRAINT channel_id_refs_id_79d66cdb FOREIGN KEY (channel_id) REFERENCES public.v2_channel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_end_id_refs_id_014ee229; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_orifice
    ADD CONSTRAINT connection_node_end_id_refs_id_014ee229 FOREIGN KEY (connection_node_end_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_end_id_refs_id_35ee1270; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_culvert
    ADD CONSTRAINT connection_node_end_id_refs_id_35ee1270 FOREIGN KEY (connection_node_end_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_end_id_refs_id_395a4016; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_channel
    ADD CONSTRAINT connection_node_end_id_refs_id_395a4016 FOREIGN KEY (connection_node_end_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_end_id_refs_id_a9965429; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pipe
    ADD CONSTRAINT connection_node_end_id_refs_id_a9965429 FOREIGN KEY (connection_node_end_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_end_id_refs_id_b2beccef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pumpstation
    ADD CONSTRAINT connection_node_end_id_refs_id_b2beccef FOREIGN KEY (connection_node_end_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_end_id_refs_id_f40dbf77; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_weir
    ADD CONSTRAINT connection_node_end_id_refs_id_f40dbf77 FOREIGN KEY (connection_node_end_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_id_refs_id_0a6435e0; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_1d_boundary_conditions
    ADD CONSTRAINT connection_node_id_refs_id_0a6435e0 FOREIGN KEY (connection_node_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_id_refs_id_114a184b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_surface_map
    ADD CONSTRAINT connection_node_id_refs_id_114a184b FOREIGN KEY (connection_node_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_id_refs_id_4f81516d; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_manhole
    ADD CONSTRAINT connection_node_id_refs_id_4f81516d FOREIGN KEY (connection_node_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_id_refs_id_55d2df40; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_1d_lateral
    ADD CONSTRAINT connection_node_id_refs_id_55d2df40 FOREIGN KEY (connection_node_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_id_refs_id_c500d603; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_impervious_surface_map
    ADD CONSTRAINT connection_node_id_refs_id_c500d603 FOREIGN KEY (connection_node_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_start_id_refs_id_014ee229; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_orifice
    ADD CONSTRAINT connection_node_start_id_refs_id_014ee229 FOREIGN KEY (connection_node_start_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_start_id_refs_id_35ee1270; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_culvert
    ADD CONSTRAINT connection_node_start_id_refs_id_35ee1270 FOREIGN KEY (connection_node_start_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_start_id_refs_id_395a4016; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_channel
    ADD CONSTRAINT connection_node_start_id_refs_id_395a4016 FOREIGN KEY (connection_node_start_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_start_id_refs_id_a9965429; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pipe
    ADD CONSTRAINT connection_node_start_id_refs_id_a9965429 FOREIGN KEY (connection_node_start_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_start_id_refs_id_b2beccef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pumpstation
    ADD CONSTRAINT connection_node_start_id_refs_id_b2beccef FOREIGN KEY (connection_node_start_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: connection_node_start_id_refs_id_f40dbf77; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_weir
    ADD CONSTRAINT connection_node_start_id_refs_id_f40dbf77 FOREIGN KEY (connection_node_start_id) REFERENCES public.v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: control_group_id_refs_id_d0f4e2d1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT control_group_id_refs_id_d0f4e2d1 FOREIGN KEY (control_group_id) REFERENCES public.v2_control_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: control_group_id_refs_id_d891225c; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control
    ADD CONSTRAINT control_group_id_refs_id_d891225c FOREIGN KEY (control_group_id) REFERENCES public.v2_control_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cross_section_definition_id_refs_id_10f5522f; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_orifice
    ADD CONSTRAINT cross_section_definition_id_refs_id_10f5522f FOREIGN KEY (cross_section_definition_id) REFERENCES public.v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cross_section_definition_id_refs_id_3168ade8; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_pipe
    ADD CONSTRAINT cross_section_definition_id_refs_id_3168ade8 FOREIGN KEY (cross_section_definition_id) REFERENCES public.v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cross_section_definition_id_refs_id_52de4c23; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_weir
    ADD CONSTRAINT cross_section_definition_id_refs_id_52de4c23 FOREIGN KEY (cross_section_definition_id) REFERENCES public.v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cross_section_definition_id_refs_id_8e4efefc; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_culvert
    ADD CONSTRAINT cross_section_definition_id_refs_id_8e4efefc FOREIGN KEY (cross_section_definition_id) REFERENCES public.v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;



--
-- Name: definition_id_refs_id_a1746ea0; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_cross_section_location
    ADD CONSTRAINT definition_id_refs_id_a1746ea0 FOREIGN KEY (definition_id) REFERENCES public.v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: global_settings_id_refs_id_295daf41; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_aggregation_settings
    ADD CONSTRAINT global_settings_id_refs_id_295daf41 FOREIGN KEY (global_settings_id) REFERENCES public.v2_global_settings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: groundwater_settings_id_refs_id_300ed996; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT groundwater_settings_id_refs_id_300ed996 FOREIGN KEY (groundwater_settings_id) REFERENCES public.v2_groundwater(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: impervious_surface_id_refs_id_001c234b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_impervious_surface_map
    ADD CONSTRAINT impervious_surface_id_refs_id_001c234b FOREIGN KEY (impervious_surface_id) REFERENCES public.v2_impervious_surface(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: interflow_settings_id_refs_id_79a59d6a; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT interflow_settings_id_refs_id_79a59d6a FOREIGN KEY (interflow_settings_id) REFERENCES public.v2_interflow(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: levee_id_refs_id_2e565295; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_connected_pnt
    ADD CONSTRAINT levee_id_refs_id_2e565295 FOREIGN KEY (levee_id) REFERENCES public.v2_levee(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: measure_group_id_refs_id_36a28871; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control
    ADD CONSTRAINT measure_group_id_refs_id_36a28871 FOREIGN KEY (measure_group_id) REFERENCES public.v2_control_measure_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: measure_group_id_refs_id_7deb88a7; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_control_measure_map
    ADD CONSTRAINT measure_group_id_refs_id_7deb88a7 FOREIGN KEY (measure_group_id) REFERENCES public.v2_control_measure_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: numerical_settings_id_refs_id_4154bad2; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT numerical_settings_id_refs_id_4154bad2 FOREIGN KEY (numerical_settings_id) REFERENCES public.v2_numerical_settings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: simple_infiltration_settings_id_refs_id_ac3bb32b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_global_settings
    ADD CONSTRAINT simple_infiltration_settings_id_refs_id_ac3bb32b FOREIGN KEY (simple_infiltration_settings_id) REFERENCES public.v2_simple_infiltration(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: surface_parameters_id_refs_id_d2471b65; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.v2_surface
    ADD CONSTRAINT surface_parameters_id_refs_id_d2471b65 FOREIGN KEY (surface_parameters_id) REFERENCES public.v2_surface_parameters(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

-- REVOKE ALL ON SCHEMA public FROM PUBLIC;
-- REVOKE ALL ON SCHEMA public FROM postgis;
-- GRANT ALL ON SCHEMA public TO postgis;
-- GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

