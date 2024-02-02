from datetime import datetime
from typing import Generic, TypeVar

from asyncua import ua

from .node import OpcuaNode

T = TypeVar("T")


class OpcuaVariable(OpcuaNode, Generic[T]):
    def __init__(self, name: str, cls: type[T], default: T):
        super().__init__(name)
        self.cls: type[T] = cls
        self.default: T = default

    async def get(self) -> T:
        value = await self.ua_node.get_value()
        assert isinstance(value, self.cls)
        return value

    async def set(self, value: T | None) -> None:
        value = value or self.default
        data_type = await self.ua_node.read_data_type_as_variant_type()
        await self.ua_node.write_value(ua.DataValue(ua.Variant(value, data_type)))

    def clone(self) -> OpcuaNode:
        return type(self)(name=self.ua_name, cls=self.cls, default=self.default)


# IDE doesn't provide auto complete if using functools.partial
class _OpcuaVar:
    def __init__(self, cls: type[T], default: T):
        self.cls = cls
        self.default = default

    def __call__(self, name: str, default: T | None = None) -> OpcuaVariable[T]:
        return OpcuaVariable(name=name, cls=self.cls, default=default or self.default)


OpcuaStrVar = _OpcuaVar(cls=str, default="")
OpcuaIntVar = _OpcuaVar(cls=int, default=0)
OpcuaFloatVar = _OpcuaVar(cls=float, default=0.0)
OpcuaBoolVar = _OpcuaVar(cls=bool, default=False)
# TODO default factory
OpcuaDatetimeVar = _OpcuaVar(cls=datetime, default=datetime.now())
