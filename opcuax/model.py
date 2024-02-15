import asyncio
from collections.abc import Generator
from typing import Any, ClassVar, Never, TypeVar

from asyncua import Node
from pydantic import BaseModel, PrivateAttr
from pydantic.fields import FieldInfo

from opcuax.helper import field_class
from opcuax.node import read_ua_variable, write_ua_variable

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)
TEnhancedModel = TypeVar("TEnhancedModel", bound="EnhancedModel")
UpdateTask = Generator[Any, None, Never]


def parse_field_class(name: str, info: FieldInfo) -> type[Any]:
    cls = info.annotation

    if cls is None:
        raise ValueError(f"field {name} must have a type annotation")

    return cls


class OpcuaModel(BaseModel):
    @classmethod
    def __pydantic_init_subclass__(cls: type["OpcuaModel"], **kwargs: Any) -> None:
        enhanced_model_class(cls)


TOpcuaModel = TypeVar("TOpcuaModel", bound=OpcuaModel)
OpcuaModelType = type[TOpcuaModel]


class EnhancedModel(BaseModel):
    classes: ClassVar[dict[type[BaseModel], type["EnhancedModel"]]] = {}
    origin: ClassVar[type[BaseModel]]
    _node: Node | None = PrivateAttr(default=None)
    _ns: int = PrivateAttr(default=0)
    _tasks: asyncio.Queue[UpdateTask] = PrivateAttr(default=None)

    async def __get_node(self, name: str) -> Node:
        assert self._node is not None
        return await self._node.get_child(f"{self._ns}:{name}")

    async def refresh(self) -> None:
        for name, info in type(self).model_fields.items():
            cls = field_class(info)
            node = await self.__get_node(name)

            if issubclass(cls, BaseModel):
                model = self.__dict__[name]
                assert isinstance(model, EnhancedModel)
                await self.__dict__[name].refresh()
            else:
                value = await read_ua_variable(node, cls)
                self.__dict__[name] = value

    @staticmethod
    def classname_for(cls: type[BaseModel]) -> str:
        return "_Opcuax" + cls.__name__

    async def __update_variable(self, name: str, value: Any) -> None:
        if value is None:
            raise ValueError("Cannot set OPC UA variable value to None")
        self.__dict__[name] = value
        node = await self.__get_node(name)
        await write_ua_variable(node, value)

    async def update_self(self, model: BaseModel) -> None:
        if not isinstance(self, type(model)):
            raise ValueError(f"Cannot update {self} by {model}")
        for name in type(self).model_fields:
            value = model.__dict__[name]

            if isinstance(value, BaseModel):
                child = self.__dict__[name]
                await child.update_self(value)
            else:
                await self.__update_variable(name, value)

    def __setattr__(self, key: str, value: Any) -> None:
        if not is_field(self, key):
            super().__setattr__(key, value)
            return

        if isinstance(value, BaseModel):
            model = self.__dict__[key]
            task = model.update_self(value)
        else:
            task = self.__update_variable(key, value)

        self._tasks.put_nowait(task)

    # TODO: how about model == enhanced?
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.origin):
            return False
        return self.__dict__ == other.__dict__


def is_field(model: EnhancedModel, name: str) -> bool:
    return name in type(model).model_fields


def enhanced_model_class(cls: type[TBaseModel]) -> type[EnhancedModel]:
    if cls in EnhancedModel.classes:
        return EnhancedModel.classes[cls]
    elif issubclass(cls, EnhancedModel):
        return cls

    new_cls: type[EnhancedModel] = type(
        EnhancedModel.classname_for(cls),
        (cls, EnhancedModel),
        {"__module__": EnhancedModel.__module__},
    )
    new_cls.origin = cls
    EnhancedModel.classes[cls] = new_cls

    for field_name, field_info in cls.model_fields.items():
        field_cls = parse_field_class(field_name, field_info)

        if issubclass(field_cls, BaseModel):
            enhanced_model_class(field_cls)
    return new_cls
