from typing import Any

from .node import OpcuaNode
from .var import OpcuaVariable


def opcua_nodes(obj: Any) -> dict[str, OpcuaNode]:
    return {
        name: attr for name, attr in obj.__dict__.items() if isinstance(attr, OpcuaNode)
    }


def _opcua_class_vars(cls: type) -> dict[str, OpcuaNode]:
    if not issubclass(cls, OpcuaObject):
        return {}
    return _opcua_class_vars(cls.__base__) | opcua_nodes(cls)


class OpcuaObject(OpcuaNode):
    @classmethod
    def opcua_class_vars(cls) -> dict[str, OpcuaNode]:
        return _opcua_class_vars(cls)

    def opcua_vars(self) -> dict[str, OpcuaNode]:
        return opcua_nodes(self)

    async def __to_dict(self, flatten: bool = False) -> dict[str, Any]:
        data = {}

        for node in self.opcua_vars().values():
            name = node.ua_name
            match node:
                case OpcuaVariable() as var:
                    data[name] = await var.get()
                case OpcuaObject() as obj:
                    sub_data = await obj.__to_dict(flatten=flatten)
                    if flatten:
                        for sub_name, sub_val in sub_data.items():
                            key = f"{name}.{sub_name}"
                            data[key] = sub_val
                    else:
                        data[name] = sub_data

        return data

    async def to_dict(self, flatten: bool = False) -> dict[str, Any]:
        return await self.__to_dict(flatten=flatten)
