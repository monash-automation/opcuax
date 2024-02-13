import asyncio
import logging
from abc import ABC
from logging import Logger
from typing import TypeVar

from asyncua import Node
from pydantic import BaseModel

from .model import EnhancedModel, TBaseModel, TOpcuaModel, UpdateTask
from .node import read_ua_variable

T = TypeVar("T")


class Opcuax(ABC):
    endpoint: str
    namespace: int
    namespace_uri: str
    logger: Logger

    ua_objects_node: Node
    objects: dict[str, EnhancedModel]
    update_tasks: asyncio.Queue[UpdateTask]

    def __init__(self, endpoint: str, namespace_uri: str) -> None:
        self.endpoint: str = endpoint
        self.namespace_uri: str = namespace_uri
        self.logger = logging.getLogger(type(self).__name__)
        self.objects = {}
        self.update_tasks = asyncio.Queue()

    def create(self, cls: type[EnhancedModel], name: str) -> EnhancedModel:
        raise NotImplementedError

    async def get_object(
        self, model_class: type[TOpcuaModel], name: str
    ) -> TOpcuaModel:
        async def dfs(
            parent: Node, cls: type[BaseModel], browse_name: str
        ) -> EnhancedModel:
            node = await parent.get_child(browse_name)
            fields = {}

            for field_name, field_info in cls.model_fields.items():
                field_browse_name = f"{self.namespace}:{field_name}"
                field_cls = field_info.annotation

                child_node = await node.get_child(field_browse_name)

                if issubclass(field_cls, BaseModel):
                    fields[field_name] = await dfs(node, field_cls, field_browse_name)
                else:
                    fields[field_name] = await read_ua_variable(child_node, field_cls)

            enhanced_cls: type[EnhancedModel] = EnhancedModel.classes[cls]
            model = enhanced_cls(**fields)
            model._tasks = self.update_tasks
            model._ns = self.namespace
            model._node = node
            assert isinstance(model, EnhancedModel)

            return model

        if name not in self.objects:
            enhanced = await dfs(
                self.ua_objects_node, model_class, f"{self.namespace}:{name}"
            )
            self.objects[name] = enhanced

        enhanced = self.objects[name]
        assert isinstance(enhanced, model_class)
        return enhanced

    async def refresh(self, model: TBaseModel) -> None:
        if not isinstance(model, EnhancedModel):
            raise ValueError("model must be an object returned from get_object()")
        await model.refresh()

    async def update(self, name: str, model: TOpcuaModel) -> TOpcuaModel:
        enhanced = await self.get_object(type(model), name)
        assert isinstance(enhanced, (EnhancedModel, type(model)))
        await enhanced.update_self(model)
        return enhanced

    async def commit(self) -> None:
        async with asyncio.TaskGroup() as tg:
            while not self.update_tasks.empty():
                task = self.update_tasks.get_nowait()
                tg.create_task(task)
