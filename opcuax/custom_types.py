from typing import Any

from asyncua import Node


async def dfs(parent: Node, fields: dict[str, Any]) -> None:
    for name, value in fields.items():
        match value:
            case dict():
                # OPC UA does not support nested types
                obj = await parent.add_object(0, name)
                await obj.set_modelling_rule(True)
                await dfs(obj, value)
            case _:
                var = await parent.add_variable(0, name, value)
                await var.set_modelling_rule(True)
                await var.set_writable(True)


async def create_object_types(
    base_object_type: Node, type_config: dict[str, Any], common_fields: dict[str, Any]
) -> dict[str, Node]:
    obj_types = {}

    for type_name, fields in type_config.items():
        obj_type: Node = await base_object_type.add_object_type(0, type_name)
        await dfs(obj_type, common_fields | fields)

        obj_types[type_name] = obj_type

    return obj_types
