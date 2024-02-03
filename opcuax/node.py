from typing import Any

from asyncua import Node, ua


class OpcuaNode:
    ua_node: Node
    ua_name: str
    ua_namespace: int

    def __init__(self, name: str, node: Node, namespace: int):
        self.ua_name = name
        self.ua_node = node
        self.ua_namespace = namespace

    def clone(self) -> "OpcuaNode":
        return type(self)(name=self.ua_name)

    @property
    def node_id(self) -> str:
        return str(self.ua_node.nodeid)


class OpcuaVarNode(OpcuaNode):
    async def read_value(self) -> Any:
        return await self.ua_node.get_value()

    async def write_value(self, value: Any) -> None:
        var_type = await self.ua_node.read_data_type_as_variant_type()
        ua_value = ua.DataValue(ua.Variant(value, var_type))
        await self.ua_node.write_value(ua_value)


class OpcuaObjNode(OpcuaNode):
    def __init__(self, name: str, node: Node, namespace: int):
        super().__init__(name, node, namespace)
        self.children: dict[str, OpcuaNode] = {}

    def add_child(self, child: OpcuaNode) -> None:
        self.__setitem__(child.ua_name, child)

    async def to_dict(self) -> dict[str, Any]:
        data = {}
        for name, child in self.children.items():
            match child:
                case OpcuaVarNode() as var:
                    data[name] = await var.read_value()
                case OpcuaObjNode() as obj:
                    data[name] = await obj.to_dict()
        return data

    async def write_values(self, data: dict[str, Any]) -> None:
        for name, child in self.children.items():
            if name not in data:
                continue
            new_value = data[name]

            match child:
                case OpcuaVarNode() as var:
                    await var.write_value(new_value)
                case OpcuaObjNode() as obj:
                    await obj.write_values(new_value)

    def __contains__(self, name: str) -> bool:
        return name in self.children

    def __getitem__(self, name: str) -> "OpcuaNode":
        return self.children[name]

    def __setitem__(self, name: str, node: OpcuaNode) -> None:
        self.children[name] = node
