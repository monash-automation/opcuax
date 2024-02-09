import logging
from abc import ABC
from collections.abc import Callable
from logging import Logger
from typing import Any, ClassVar, TypeVar

from asyncua import Node
from pydantic import BaseModel

from .models import OpcuaObjects
from .node import OpcuaObjNode, OpcuaVarNode, make_object

_OpcuaObjects = TypeVar("_OpcuaObjects", bound=OpcuaObjects)
_Undefined: tuple = ()


class OpcuaModel(BaseModel):
    __node__: ClassVar[tuple] = _Undefined

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: dict[str, Any]) -> None:
        print(f"pydantic init subclass {cls.__name__}")


_OpcuaModel = TypeVar("_OpcuaModel", bound="OpcuaModel")


class Opcuax(ABC):
    endpoint: str
    namespace: int
    namespace_uri: str
    logger: Logger

    ua_objects_node: Node
    objects_node: OpcuaObjNode

    def __init__(self, endpoint: str, namespace_uri: str):
        self.endpoint: str = endpoint
        self.namespace_uri: str = namespace_uri
        self.logger = logging.getLogger(type(self).__name__)

    async def create_opcua_nodes(self, objects_cls: type[OpcuaObjects]) -> None:
        async def dfs(parent_node: OpcuaObjNode, cls: type[BaseModel]) -> None:
            ua_nodes = await parent_node.ua_node.get_children()

            for ua_node in ua_nodes:
                name = (await ua_node.read_display_name()).Text

                if name not in cls.model_fields:
                    continue
                elif name in parent_node:
                    # already created opcua nodes
                    continue

                field = cls.model_fields[name]
                field_cls = field.annotation
                assert field_cls is not None

                if issubclass(field_cls, BaseModel):
                    obj_node = OpcuaObjNode(name, ua_node, self.namespace)
                    parent_node.add_child(obj_node)
                    await dfs(obj_node, field_cls)
                else:
                    var_node = OpcuaVarNode(name, ua_node, self.namespace, field)
                    parent_node.add_child(var_node)

        await dfs(self.objects_node, objects_cls)

    async def read_objects(self, cls: type[_OpcuaObjects]) -> _OpcuaObjects:
        await self.create_opcua_nodes(cls)
        data = await self.objects_node.to_dict()
        return cls(**data)

    async def update_objects(self, objects: _OpcuaObjects) -> None:
        await self.objects_node.write_values(objects.model_dump())

    def create_node_tree(self, cls: type[_OpcuaModel]) -> None:
        if cls.__node__ is _Undefined:
            cls.__node__ = make_object(cls, self.namespace)

    async def get(
        self, name: str, cls: type[OpcuaModel], expr: Callable[[OpcuaModel], Any]
    ) -> Any:
        node = expr(cls.__node__)
        root = await self.objects_node.ua_node.get_child(f"{self.namespace}:{name}")
        return await node.read_value(root)

    async def set(
        self,
        name: str,
        cls: type[OpcuaModel],
        value: Any,
        expr: Callable[[OpcuaModel], Any],
    ) -> None:
        node = expr(cls.__node__)
        root = await self.objects_node.ua_node.get_child(f"{self.namespace}:{name}")
        await node.write_value(root, value)
