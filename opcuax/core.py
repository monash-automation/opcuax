import logging
from abc import ABC
from collections.abc import Callable
from logging import Logger
from typing import Any, ClassVar, TypeVar

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


class Opcuax(ABC):
    endpoint: str
    namespace: int
    namespace_uri: str
    logger: Logger

    ua_objects_node: Node

    def __init__(self, endpoint: str, namespace_uri: str):
        self.endpoint: str = endpoint
        self.namespace_uri: str = namespace_uri
        self.logger = logging.getLogger(type(self).__name__)

    def create_node_tree(self, cls: type[_OpcuaModel]) -> None:
        if cls.__node__ is _UndefinedNode:
            cls.__node__ = make_object(cls, self.namespace)

    async def get(
        self,
        cls: type[_OpcuaModel],
        name: str,
        expr: Callable[[_OpcuaModel], T] = _identity,
    ) -> T:
        self.create_node_tree(cls)
        node = expr(cls.__node__)
        root = await self.ua_objects_node.get_child(f"{self.namespace}:{name}")
        return await node.read_value(root)

    async def set(
        self,
        cls: type[_OpcuaModel],
        name: str,
        value: Any,
        expr: Callable[[_OpcuaModel], Any] = _identity,
    ) -> None:
        self.create_node_tree(cls)
        node = expr(cls.__node__)
        root = await self.ua_objects_node.get_child(f"{self.namespace}:{name}")
        await node.write_value(root, value)
