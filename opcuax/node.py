from collections import namedtuple
from typing import Any, NamedTuple

from asyncua import Node, ua
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from opcuax.values import opcua_value_of


class Variable:
    __slots__ = ("browse_name", "cls")

    def __init__(self, browse_name: str, cls: type[Any]):
        self.browse_name: str = browse_name
        self.cls: type[Any] = cls

    async def read_value(self, root: Node) -> Any:
        node = await root.get_child(self.browse_name)
        value = await node.read_value()
        return self.cls(value)

    async def write_value(self, root: Node, value: Any) -> None:
        opcua_value = value
        if not issubclass(self.cls, (str, int, float, bool)):
            opcua_value = str(value)
        node = await root.get_child(self.browse_name)
        var_type = await node.read_data_type_as_variant_type()
        ua_value = ua.DataValue(ua.Variant(opcua_value, var_type))
        await node.write_value(ua_value)


async def _write_value(self: NamedTuple, root: Node, obj: BaseModel) -> None:
    for name, node in zip(self._fields, self):
        value = getattr(obj, name)
        await node.write_value(root, value)


def object_classname(cls: type[BaseModel]) -> str:
    return f"_{cls.__name__}Object"


# TODO: add root to class name to avoid name collision
def make_object(cls: type[BaseModel], ns: int, path: str = "") -> tuple:
    field_names, values = [], []

    for name, field in cls.model_fields.items():
        field_cls = field.annotation
        field_names.append(name)
        browse_name = f"{path}/{ns}:{name}"

        if issubclass(field_cls, BaseModel):
            child_obj = make_object(field_cls, ns, browse_name)
            values.append(child_obj)
        else:
            values.append(Variable(browse_name, field_cls))

    object_cls = namedtuple(object_classname(cls), field_names)

    async def _read_value(self: NamedTuple, root: Node) -> Any:
        data = {
            name: await node.read_value(root) for name, node in zip(self._fields, self)
        }
        return cls(**data)

    object_cls.read_value = _read_value
    object_cls.write_value = _write_value

    return object_cls(*values)


class OpcuaNode:
    ua_node: Node
    ua_name: str
    ua_namespace: int

    def __init__(self, name: str, node: Node, namespace: int):
        self.ua_name = name
        self.ua_node = node
        self.ua_namespace = namespace

    @property
    def node_id(self) -> str:
        return str(self.ua_node.nodeid)


class OpcuaVarNode(OpcuaNode):
    field_info: FieldInfo

    def __init__(self, name: str, node: Node, namespace: int, field_info: FieldInfo):
        super().__init__(name, node, namespace)
        self.field_info = field_info

    async def read_value(self) -> Any:
        return await self.ua_node.get_value()

    async def write_value(self, value: Any) -> None:
        opcua_value = opcua_value_of(value, self.field_info)
        var_type = await self.ua_node.read_data_type_as_variant_type()
        ua_value = ua.DataValue(ua.Variant(opcua_value, var_type))
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
