from typing import Any, List, Dict


def strip_dict_none_values(value: Any):
    if isinstance(value, List):
        for x in value:
            strip_dict_none_values(x)
    if isinstance(value, Dict):
        to_delete = []
        for k, v in value.items():
            if v == None:
                to_delete.append(k)
            else:
                strip_dict_none_values(v)

        for x in to_delete:
            del value[x]
