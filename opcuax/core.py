import logging
from abc import ABC
from logging import Logger
from typing import TypeVar

from asyncua import Node
from pydantic import BaseModel

from .models import OpcuaObjects
from .node import OpcuaObjNode, OpcuaVarNode

_OpcuaObjects = TypeVar("_OpcuaObjects", bound=OpcuaObjects)


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

                if issubclass(field_cls, BaseModel):
                    node = OpcuaObjNode(name, ua_node, self.namespace)
                    await dfs(node, field_cls)
                else:
                    node = OpcuaVarNode(name, ua_node, self.namespace, field)

                parent_node.add_child(node)

        await dfs(self.objects_node, objects_cls)

    async def read_objects(self, cls: type[_OpcuaObjects]) -> _OpcuaObjects:
        await self.create_opcua_nodes(cls)
        data = await self.objects_node.to_dict()
        return cls(**data)

    async def update_objects(self, objects: _OpcuaObjects) -> None:
        await self.objects_node.write_values(objects.model_dump())
