import asyncio
import copy
import logging
from abc import ABC
from collections.abc import Awaitable, Callable
from logging import Logger
from typing import Any, ClassVar, Generic, TypeVar

from asyncua import Node, ua
from pydantic import BaseModel

from .values import python_value

_UndefinedNode: tuple = ()
T = TypeVar("T")
_BaseModel = TypeVar("_BaseModel", bound=BaseModel)


__node_class_prefix: str = "_Opcuax"


def __node_classname(cls: type[_BaseModel]) -> str:
    return __node_class_prefix + cls.__name__


class OpcuaxNode(Generic[T]):
    __model_fields__: set[str]
    __slots__ = ("cls", "browse_path", "updates", "__model_fields__")

    def __init__(
        self,
        cls: type[T],
        browse_path: list[str],
        updates: list[Callable[[Node, int], Awaitable[None]]] | None = None,
    ) -> None:
        super().__init__()
        self.cls: type[T] = cls
        self.browse_path: list[str] = browse_path
        self.updates: list[Callable[[Node, int], Awaitable[None]]] = updates

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(cls={self.cls}, "
            f"browse_path={self.browse_path}, updates={self.updates})"
        )

    def is_object_node(self) -> bool:
        return issubclass(self.cls, BaseModel)

    def _browse_path(self, ns: int) -> str:
        return "/".join([f"{ns}:{name}" for name in self.browse_path])

    async def _get_ua_node(self, root: Node, ns: int) -> Node:
        return await root.get_child(self._browse_path(ns))

    async def read(self, root: Node, ns: int = 0) -> T:
        if issubclass(self.cls, BaseModel):
            return await self.read_object(root, ns)
        else:
            return await self.read_variable(root, ns)

    async def read_variable(self, root: Node, ns: int = 0) -> T:
        node = await self._get_ua_node(root, ns)
        value = await node.read_value()
        return python_value(self.cls, value)

    async def read_object(self, root: Node, ns: int = 0) -> T:
        data = {}

        for name in self.__model_fields__:
            if name.startswith("_"):
                continue
            child = getattr(self, name)
            data[name] = await child.read(root, ns)

        return self.cls(**data)

    def _write_variable(self, value: Any) -> Callable[[Node, int], Awaitable[None]]:
        # TODO extract to values
        opcua_value = value
        if not issubclass(self.cls, (str, int, float, bool)):
            opcua_value = str(value)

        async def _write(root: Node, ns: int) -> None:
            node = await self._get_ua_node(root, ns)
            var_type = await node.read_data_type_as_variant_type()
            ua_value = ua.DataValue(ua.Variant(opcua_value, var_type))
            await node.write_value(ua_value)

        self.updates.append(_write)
        return _write

    def _write_object(self, obj: _BaseModel) -> None:
        for name in self.__model_fields__:
            if name.startswith("_"):
                continue
            # child = getattr(self, name)
            value = getattr(obj, name)
            node = getattr(self, name)
            node.write(value)

    def write(self, value: Any) -> None:
        if issubclass(self.cls, BaseModel):
            self._write_object(value)
        else:
            self._write_variable(value)

    def __get__(self, instance: _BaseModel | None, owner: type[Any]) -> "OpcuaxNode[T]":
        if instance is None:  # access from class
            return self

        assert instance.updates is not None

        node = copy.copy(self)
        node.browse_path = [*instance.browse_path, *self.browse_path]
        node.updates = instance.updates
        return node

    def __set__(self, instance: "OpcuaxNode", value: Any) -> None:
        if instance is None:
            return
        node = copy.copy(self)
        node.browse_path = [*instance.browse_path, *self.browse_path]
        node.updates = instance.updates
        node.write(value)


def create_node_class(cls: type[T], **kwargs) -> type[OpcuaxNode[T]]:
    if cls.__name__.startswith(__node_class_prefix):
        return cls
    elif cls in OpcuaModel.__node_classes__:
        return OpcuaModel.__node_classes__[cls]

    descriptors = {}

    for field_name, field in cls.model_fields.items():
        field_cls = field.annotation
        assert field_cls is not None

        if issubclass(field_cls, BaseModel):
            sub_cls = create_node_class(field_cls)
            descriptors[field_name] = sub_cls(cls=field_cls, browse_path=[field_name])
        else:
            descriptors[field_name] = OpcuaxNode[field_cls](
                cls=field_cls, browse_path=[field_name]
            )

    node_cls_name = __node_classname(cls)
    new_dict = {
        "__module__": cls.__module__,
        "__qualname__": node_cls_name,
        "__model_fields__": descriptors.keys(),
        **descriptors,
        **kwargs,
    }

    node_cls = type[OpcuaxNode[cls]](node_cls_name, (OpcuaxNode,), new_dict)
    OpcuaModel.__node_classes__[cls] = node_cls
    return node_cls


class OpcuaModel(BaseModel):
    __node_classes__: ClassVar[dict[type[OpcuaxNode], type[OpcuaxNode]]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        create_node_class(cls)


_OpcuaModel = TypeVar("_OpcuaModel", bound="OpcuaModel")


def _identity(model: _OpcuaModel) -> _OpcuaModel:
    return model


class OpcuaObject(Generic[_OpcuaModel]):
    def __init__(
        self, opcuax: "Opcuax", model_cls: type[_OpcuaModel], name: str
    ) -> None:
        self.opcuax: "Opcuax" = opcuax
        self.model_cls: type[_OpcuaModel] = model_cls
        self.name = name

    def __browse_name(self) -> str:
        return f"{self.opcuax.namespace}:{self.name}"

    async def __get_node(self, browse_name: str) -> Node:
        return await self.opcuax.ua_objects_node.get_child(browse_name)


def fetch(cls: type[_OpcuaModel], name: str) -> _OpcuaModel:
    return OpcuaModel.__node_classes__[cls](browse_path=[name], updates=[], cls=cls)


class Opcuax(ABC):
    endpoint: str
    namespace: int
    namespace_uri: str
    logger: Logger

    ua_objects_node: Node

    def __init__(self, endpoint: str, namespace_uri: str) -> None:
        self.endpoint: str = endpoint
        self.namespace_uri: str = namespace_uri
        self.logger = logging.getLogger(type(self).__name__)

    def create(self, cls: type[_OpcuaModel], name: str) -> _OpcuaModel:
        raise NotImplementedError

    async def read(self, node: T) -> T:
        return await node.read(self.ua_objects_node, self.namespace)

    async def update(self, name: str, model: OpcuaModel) -> _OpcuaModel:
        node = fetch(type(model), name)
        node._write_object(model)
        await self.commit(node)
        return node

    async def commit(self, node: OpcuaModel) -> None:
        async with asyncio.TaskGroup() as tg:
            for fn in node.updates:
                tg.create_task(fn(self.ua_objects_node, self.namespace))
        node.updates.clear()
