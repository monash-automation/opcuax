from typing import Type, TypeVar

from asyncua import Client, Node, ua


class OpcuaNode:
    ua_node: Node

    def __init__(self, name: str):
        self.name = name

    def clone(self):
        return type(self)(name=self.name)


class OpcuaVariable(OpcuaNode):
    async def get(self):
        return await self.ua_node.get_value()

    async def set(self, value):
        data_type = await self.ua_node.read_data_type_as_variant_type()
        await self.ua_node.write_value(ua.DataValue(ua.Variant(value, data_type)))


class OpcuaObject(OpcuaNode):
    pass


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
