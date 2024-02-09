from collections import namedtuple
from typing import Any, NamedTuple

from asyncua import Node, ua
from pydantic import BaseModel

from opcuax.values import python_value


class Variable:
    __slots__ = ("browse_name", "cls")

    def __init__(self, browse_name: str, cls: type[Any]):
        self.browse_name: str = browse_name
        self.cls: type[Any] = cls

    async def read_value(self, root: Node) -> Any:
        node = await root.get_child(self.browse_name)
        value = await node.read_value()
        return python_value(self.cls, value)

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
        assert field_cls is not None

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
