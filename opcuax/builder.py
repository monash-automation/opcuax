from typing import Any

from asyncua import Node, Server, ua
from asyncua.ua import Int16, String


class TypeBuilder:
    def __init__(self, server: Server):
        self.server = server
        self.types: dict[str, Node] = {}
        self.next_type_ns = self.server.get_root_node().nodeid.NamespaceIndex + 1

    async def parse_types(
        self, types: dict[str, Any], base_fields: dict[str, str]
    ) -> dict[str, Node]:
        built = {}

        for type_name, categories in types.items():
            tp = await self.create_type(type_name)

            for name, default in base_fields.items():
                await create_field(tp, name, default)

            for cat_name, fields in categories.items():
                cat = await create_sub_object(tp, cat_name)

                for field_name, default in fields.items():
                    await create_field(cat, field_name, default, add_prefix=True)

            built[type_name] = tp

        return built

    async def create_type(self, name: str) -> Node:
        node_id = ua.NodeId(String(name), Int16(self.next_type_ns))
        self.next_type_ns += 1
        return await self.server.nodes.base_object_type.add_object_type(
            nodeid=node_id, bname=name
        )


async def create_sub_object(parent: Node, name: str) -> Node:
    node_id = ua.NodeId(String(name), Int16(parent.nodeid.NamespaceIndex))
    cat = await parent.add_object(node_id, name)
    await cat.set_modelling_rule(True)
    return cat


async def create_field(parent: Node, name: str, default: Any, add_prefix=False) -> Node:
    if add_prefix:
        prefix = parent.nodeid.Identifier[0].upper()
        name = f"{prefix}_{name}"
    node_id = ua.NodeId(String(name), Int16(parent.nodeid.NamespaceIndex))
    var = await parent.add_variable(node_id, name, default)
    await var.set_writable(True)
    await var.set_modelling_rule(True)
    return var
