from typing import List, Dict, Union
from sqlalchemy.orm import Query
from sqlalchemy.orm.session import Session
from threedi_api_client.openapi.models.timed_structure_control import (
    TimedStructureControl,
)
from threedi_api_client.openapi.models.measure_location import MeasureLocation
from threedi_api_client.openapi.models.measure_specification import MeasureSpecification
from threedi_api_client.openapi.models.table_structure_control import (
    TableStructureControl,
)
from threedi_api_client.openapi.models.memory_structure_control import (
    MemoryStructureControl,
)
from threedi_modelchecker.simulation_templates.exceptions import SchematisationError
from threedi_modelchecker.simulation_templates.utils import strip_dict_none_values
from threedi_modelchecker.threedi_model.models import (
    Control,
    ControlGroup,
    ControlMeasureGroup,
    ControlMeasureMap,
    ControlMemory,
    ControlTimed,
    ControlTable,
)
from threedi_modelchecker.simulation_templates.models import StructureControls


def control_measure_map_to_measure_location(
    c_measure_map: ControlMeasureMap,
) -> MeasureLocation:
    # Connection nodes should be only option here.
    CONTENT_TYPE_MAP = {"v2_connection_nodes": "v2_connection_node"}

    return MeasureLocation(
        weight=str(c_measure_map.weight),
        content_type=CONTENT_TYPE_MAP[c_measure_map.object_type],
        content_pk=c_measure_map.object_id,
    )


def to_measure_specification(
    control: Union[ControlMemory, ControlTable],
    group: ControlGroup,
    locations: List[MeasureLocation],
) -> MeasureSpecification:
    VARIABLE_MAPPING = {
        "waterlevel": "s1",
        "volume": "vol1",
        "discharge": "q",
        "velocity": "u1",
    }

    # Use > as default for memory control
    operator = ">"
    if hasattr(control, "measure_operator"):
        operator = control.measure_operator

    return MeasureSpecification(
        name=group.name[:50],
        variable=VARIABLE_MAPPING[control.measure_variable],
        locations=locations,
        operator=operator,
    )


TYPE_MAPPING = {"set_capacity": "set_pump_capacity"}
CAPACITY_FACTOR: float = 0.001


def to_table_control(
    control: Control,
    table_control: ControlTable,
    measure_specification: MeasureSpecification,
) -> TableStructureControl:

    action_type: str = TYPE_MAPPING.get(
        table_control.action_type, table_control.action_type
    )
    # Note: Yes, table control really uses # and ;
    try:
        values = [
            [float(y) for y in x.split(";")]
            for x in table_control.action_table.split("#")
        ]
        if table_control.action_type == "set_capacity":
            values[1] = [x * CAPACITY_FACTOR for x in values[1]]
    except (ValueError, TypeError):
        raise SchematisationError(
            f"Table control action_table incorrect format for v2_control_table.id = {table_control.id}"
        )

    try:
        control_start = int(control.start)
    except (ValueError, TypeError):
        control_start = 0

    try:
        int(control.end)
    except (ValueError, TypeError):
        raise SchematisationError(
            f"Timed control control.end not set for v2_control_table.id = {table_control.id}"
        )

    return TableStructureControl(
        offset=control_start,
        duration=int(control.end) - control_start,
        measure_specification=measure_specification,
        structure_id=table_control.target_id,
        structure_type=table_control.target_type,
        type=action_type,
        values=values,
    )


def to_memory_control(
    control: Control,
    memory_control: ControlMemory,
    measure_specification: MeasureSpecification,
) -> MemoryStructureControl:

    action_type: str = TYPE_MAPPING.get(
        memory_control.action_type, memory_control.action_type
    )

    try:
        value = [float(x) for x in memory_control.action_value.split(" ")]
    except (ValueError, TypeError):
        raise SchematisationError(
            f"Memory control action_value incorrect format for v2_control_memory.id = {memory_control.id}"
        )

    try:
        control_start = int(control.start)
    except (ValueError, TypeError):
        control_start = 0

    try:
        int(control.end)
    except (ValueError, TypeError):
        raise SchematisationError(
            f"Timed control control.end not set for v2_control_memory.id = {memory_control.id}"
        )

    return MemoryStructureControl(
        offset=control_start,
        duration=int(control.end) - control_start,
        measure_specification=measure_specification,
        structure_id=memory_control.target_id,
        structure_type=memory_control.target_type,
        type=action_type,
        value=value,
        upper_threshold=float(memory_control.upper_threshold),
        lower_threshold=float(memory_control.lower_threshold),
        is_inverse=bool(memory_control.is_inverse),
        is_active=bool(memory_control.is_active),
    )


def to_timed_control(
    control: Control, timed_control: ControlTimed
) -> TimedStructureControl:

    action_type: str = TYPE_MAPPING.get(
        timed_control.action_type, timed_control.action_type
    )

    try:
        values = [
            [float(y) for y in x.split(";")]
            for x in timed_control.action_table.split("#")
        ]

        if timed_control.action_type == "set_capacity":
            values[1] = [x * CAPACITY_FACTOR for x in values[1]]

    except (ValueError, TypeError):
        raise SchematisationError(
            f"Timed control action_table incorrect format for v2_control_timed.id = {timed_control.id}"
        )

    try:
        control_start = int(control.start)
    except (ValueError, TypeError):
        control_start = 0

    try:
        int(control.end)
    except (ValueError, TypeError):
        raise SchematisationError(
            f"Timed control control.end not set for v2_control_timed.id = {timed_control.id}"
        )

    # Pick first two values
    value = values[0]

    return TimedStructureControl(
        offset=control_start,
        duration=int(control.end) - control_start,
        value=value,
        type=action_type,
        structure_id=timed_control.target_id,
        structure_type=timed_control.target_type,
    )


class StructureControlExtractor(object):
    def __init__(self, session: Session, control_group_id: int):
        self.session = session
        self._controls = None
        self._control_group_id = control_group_id

    def __initialize_controls(self):
        if self._controls is None:
            self._controls = {"timed": [], "table": [], "memory": []}
            table_lookup = dict(
                [
                    (x.id, x)
                    for x in Query(ControlTable).with_session(self.session).all()
                ]
            )
            memory_lookup = dict(
                [
                    (x.id, x)
                    for x in Query(ControlMemory).with_session(self.session).all()
                ]
            )
            timed_lookup = dict(
                [
                    (x.id, x)
                    for x in Query(ControlTimed).with_session(self.session).all()
                ]
            )
            maps_lookup = {}

            for map_item in Query([ControlMeasureMap]).with_session(self.session).all():
                if map_item.measure_group_id not in maps_lookup:
                    maps_lookup[map_item.measure_group_id] = []
                maps_lookup[map_item.measure_group_id].append(
                    control_measure_map_to_measure_location(map_item)
                )

            all_controls = (
                Query([Control, ControlGroup, ControlMeasureGroup])
                .join(ControlGroup, ControlMeasureGroup)
                .with_session(self.session)
                .filter(
                    Control.control_group_id == self._control_group_id,
                    ControlGroup.id == self._control_group_id,
                )
                .all()
            )

            for control, group, measuregroup in all_controls:
                control: Control
                maps: List[ControlMeasureGroup] = maps_lookup[measuregroup.id]

                api_control = None

                if control.control_type == "table":
                    table: ControlTable = table_lookup[control.control_id]
                    measure_spec = to_measure_specification(table, group, maps)
                    api_control = to_table_control(control, table, measure_spec)
                elif control.control_type == "memory":
                    memory: ControlMemory = memory_lookup[control.control_id]
                    measure_spec = to_measure_specification(memory, group, maps)
                    api_control = to_memory_control(control, memory, measure_spec)
                else:
                    continue
                self._controls[control.control_type].append(api_control)

            for control in (
                Query(Control)
                .filter(
                    Control.control_type == "timed",
                    Control.control_group_id == self._control_group_id,
                )
                .with_session(self.session)
                .all()
            ):

                timed: ControlTimed = timed_lookup[control.control_id]
                api_control = to_timed_control(control, timed)
                self._controls[control.control_type].append(api_control)

    def all_controls(self) -> StructureControls:
        self.__initialize_controls()
        return StructureControls(**self._controls)

    @property
    def memory_controls(self) -> List[MemoryStructureControl]:
        self.__initialize_controls()
        return self._controls["memory"]

    @property
    def timed_controls(self) -> List[TimedStructureControl]:
        self.__initialize_controls()
        return self._controls["timed"]

    @property
    def table_controls(self) -> List[TableStructureControl]:
        self.__initialize_controls()
        return self._controls["table"]

    def as_list(self) -> List[Dict]:
        controls = []
        for control in self.all_controls():
            control_dict = control.to_dict()
            strip_dict_none_values(control_dict)
            controls.append(control_dict)
        return controls
