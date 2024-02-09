import logging
from abc import ABC
from collections.abc import Callable
from logging import Logger
from typing import Any, ClassVar, Generic, TypeVar

from asyncua import Node
from pydantic import BaseModel

from .node import make_object

_UndefinedNode: tuple = ()


class OpcuaModel(BaseModel):
    __node__: ClassVar[tuple] = _UndefinedNode


_OpcuaModel = TypeVar("_OpcuaModel", bound="OpcuaModel")
T = TypeVar("T")


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

    async def get(self, select: Callable[[_OpcuaModel], T] = _identity) -> T:
        self.opcuax.create_node_tree(self.model_cls)
        node = select(self.model_cls.__node__)
        ua_root = await self.__get_node(self.__browse_name())
        return await node.read_value(ua_root)

    async def set(
        self,
        value: T,
        select: Callable[[_OpcuaModel], T] = _identity,
    ) -> None:
        self.opcuax.create_node_tree(self.model_cls)
        node = select(self.model_cls.__node__)
        ua_root = await self.__get_node(self.__browse_name())
        await node.write_value(ua_root, value)


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

    def create_node_tree(self, cls: type[_OpcuaModel]) -> None:
        if cls.__node__ is _UndefinedNode:
            cls.__node__ = make_object(cls, self.namespace)

    def get_object(self, cls: type[_OpcuaModel], name: str) -> OpcuaObject:
        return OpcuaObject(self, cls, name)

    async def get(
        self,
        cls: type[_OpcuaModel],
        name: str,
        select: Callable[[_OpcuaModel], T] = _identity,
    ) -> T:
        self.create_node_tree(cls)
        node = select(cls.__node__)
        root = await self.ua_objects_node.get_child(f"{self.namespace}:{name}")
        return await node.read_value(root)

    async def set(
        self,
        cls: type[_OpcuaModel],
        name: str,
        value: Any,
        select: Callable[[_OpcuaModel], Any] = _identity,
    ) -> None:
        self.create_node_tree(cls)
        node = select(cls.__node__)
        root = await self.ua_objects_node.get_child(f"{self.namespace}:{name}")
        await node.write_value(root, value)
