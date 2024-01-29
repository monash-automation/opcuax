from typing import Generic, TypeVar

from asyncua import Client, Node, ua


class OpcuaNode:
    ua_node: Node

    def __init__(self, name: str):
        self.name = name

    def clone(self):
        return type(self)(name=self.name)


_Value = TypeVar("_Value", int, str, float, bool)


class OpcuaVariable(OpcuaNode, Generic[_Value]):
    async def get(self) -> _Value:
        return await self.ua_node.get_value()

    async def set(self, value: _Value) -> None:
        data_type = await self.ua_node.read_data_type_as_variant_type()
        await self.ua_node.write_value(ua.DataValue(ua.Variant(value, data_type)))


class OpcuaObject(OpcuaNode):
    async def __to_dict(self, parent_name: str | None = None) -> dict:
        data = {}
        for name, attr in self.__dict__.items():
            key = name if parent_name is None else f"{parent_name}_{name}"
            match attr:
                case OpcuaVariable() as var:
                    data[key] = await var.get()
                case OpcuaObject() as obj:
                    sub_fields = await obj.__to_dict(parent_name=key)
                    data.update(sub_fields)

        return data

    async def to_dict(self):
        return await self.__to_dict()


_OpcuaObject = TypeVar("_OpcuaObject", bound=OpcuaObject)


class OpcuaClient(Client):
    async def set_ua_node(self, parent: Node, node: OpcuaNode):
        node.ua_node = await parent.get_child(node.name)

        if not isinstance(node, OpcuaObject):
            return

        for name, attr in type(node).__dict__.items():
            if not isinstance(attr, OpcuaNode):
                continue
            child = attr.clone()
            setattr(node, name, child)
            await self.set_ua_node(node.ua_node, child)

    async def get_object(self, cls: type[_OpcuaObject], name: str) -> _OpcuaObject:
        obj = cls(name)
        await self.set_ua_node(self.get_objects_node(), obj)
        return obj
