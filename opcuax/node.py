from typing import Any, TypeVar

from asyncua import Node, ua

from opcuax.values import opcua_value, python_value

T = TypeVar("T")


async def read_ua_variable(node: Node, cls: type[T]) -> T:
    ua_value = await node.read_value()
    value = python_value(cls, ua_value)
    return value  # type: ignore


async def write_ua_variable(node: Node, value: Any) -> None:
    value = opcua_value(value)
    var_type = await node.read_data_type_as_variant_type()
    ua_value = ua.DataValue(ua.Variant(value, var_type))
    await node.write_value(ua_value)
