# %% 
from typing import List, Union
from threedi_api_client.openapi.models.timed_structure_control import TimedStructureControl
from threedi_modelchecker.threedi_model.models import Control, ControlGroup, ControlMeasureGroup, ControlMeasureMap, ControlMemory, ControlTimed, ControlTable
from threedi_modelchecker.threedi_database import ThreediDatabase
from sqlalchemy.orm import Query


from threedi_api_client.openapi.models.measure_location import MeasureLocation
from threedi_api_client.openapi.models.measure_specification import MeasureSpecification
from threedi_api_client.openapi.models.table_structure_control import TableStructureControl
from threedi_api_client.openapi.models.memory_structure_control import MemoryStructureControl


# %%
sqlite_file = "/srv/nens/models/t0224_velsen_velsen_noord/92e041d46a810d97fd6120ffa5ba0b81935f5d0d/velsen_noord_1d2d.sqlite"
database = ThreediDatabase(
    connection_settings={"db_path": sqlite_file}, db_type="spatialite"
)

session = database.get_session()
# %%

data = Query([Control, ControlGroup, ControlMeasureGroup]).join(ControlGroup, ControlMeasureGroup).with_session(session).all()

def control_measure_map_to_measure_location(c_measure_map: ControlMeasureMap) -> MeasureLocation:
    # Connection nodes should be only option here.
    CONTENT_TYPE_MAP = {
        "v2_connection_nodes": "v2_connection_node"
    }

    return MeasureLocation(
        weight=str(c_measure_map.weight), 
        content_type=CONTENT_TYPE_MAP[c_measure_map.object_type], 
        content_pk=c_measure_map.object_id
    )


def to_measure_specification(control: Union[ControlMemory, ControlTable], group: ControlGroup, locations: List[MeasureLocation]) -> MeasureSpecification:
    VARIABLE_MAPPING = {
        "waterlevel": "s1",
        "volume": "vol1",
        "discharge": "q",
        "velocity": "u1"
    }

    # Use > as default for memory control
    operator = ">"
    if hasattr(control, "measure_operator"):
        operator = control.measure_operator

    return MeasureSpecification(
        name=group.name[:50],
        variable=VARIABLE_MAPPING[control.measure_variable],
        locations=locations,
        operator=operator
    )

def to_table_control(control: Control, table_control: ControlTable, measure_specification: MeasureSpecification) -> TableStructureControl:
    # Note: Table control really uses # and ; 
    values = [[float(y) for y in x.split(";")] for x in table_control.action_table.split('#')]

    return TableStructureControl(
        offset=int(control.start),
        duration=int(control.end) - int(control.start),
        measure_specification=measure_specification,
        structure_id=table_control.target_id,
        structure_type=table_control.target_type,
        type=table_control.action_type,
        values=values
    )


def to_memory_control(control: Control, memory_control: ControlMemory, measure_specification: MeasureSpecification) -> MemoryStructureControl:
    value = [float(x) for x in memory_control.action_value.split(" ")]

    return MemoryStructureControl(
        offset=int(control.start),
        duration=int(control.end) - int(control.start),
        measure_specification=measure_specification,
        structure_id=memory_control.target_id,
        structure_type=memory_control.target_type,
        type=memory_control.action_type,
        value=value,
        upper_threshold=float(memory_control.upper_threshold),
        lower_threshold=float(memory_control.lower_threshold),
        is_inverse=bool(memory_control.is_inverse),
        is_active=bool(memory_control.is_active)
    )


def to_timed_control(control: Control, timed_control: ControlTimed) -> TimedStructureControl:
    # TODO: check this format
    value = [float(x) for x in timed_control.action_table.split(" ")]

    return TimedStructureControl(
        offset=int(control.start),
        duration=int(control.end) - int(control.start),
        value=value,
        type=timed_control.action_type,
        structure_id=timed_control.target_id,
        structure_type=timed_control.target_type,
    )


table_lookup = dict([(x.id, x) for x in Query(ControlTable).with_session(session).all()])
memory_lookup = dict([(x.id, x) for x in Query(ControlMemory).with_session(session).all()])
timed_lookup = dict([(x.id, x) for x in Query(ControlTimed).with_session(session).all()])


maps_lookup = {}

for map_item in Query([ControlMeasureMap]).with_session(session).all():
    if map_item.measure_group_id not in maps_lookup:
        maps_lookup[map_item.measure_group_id] = []
    maps_lookup[map_item.measure_group_id].append(
        control_measure_map_to_measure_location(map_item))


for control, group, measuregroup in data:
    control: Control
    maps: List[ControlMeasureGroup] = maps_lookup[measuregroup.id]

    api_control = None

    if control.control_type == 'table':
        table: ControlTable = table_lookup[control.control_id]
        measure_spec = to_measure_specification(table, group, maps)
        api_control = to_table_control(control, table, measure_spec)
    elif control.control_type == 'memory':
        memory: ControlMemory = memory_lookup[control.control_id]
        measure_spec = to_measure_specification(memory, group, maps)
        api_control = to_memory_control(control, memory, measure_spec)
    elif control.control_type == "timed":
        timed: ControlTimed = memory_lookup[control.control_id]
        api_control = to_timed_control(control, timed)
    else:
        raise Exception("Unknown control_type %s", control.control_type)

    print(api_control)

# %%

# %%
