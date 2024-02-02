from types import TracebackType
from typing import TypeVar

from asyncua import Client, Node

from .obj import OpcuaObject

T = TypeVar("T", bound=OpcuaObject)


class OpcuaClient:
    client: Client
    objects: dict[str, OpcuaObject]
    server_namespace: str
    namespace_index: int

    def __init__(self, url: str, server_namespace: str):
        self.client: Client = Client(url)
        self.objects = {}
        self.server_namespace = server_namespace

    async def __init_fields(self, obj: OpcuaObject) -> None:
        for name, attr in obj.opcua_class_vars().items():
            child = attr.clone()
            child.ua_node = await obj.ua_node.get_child(
                f"{self.namespace_index}:{child.ua_name}"
            )
            setattr(obj, name, child)

            if isinstance(child, OpcuaObject):
                await self.__init_fields(child)

    async def create_object(self, cls: type[T], name: str) -> T:
        obj = cls(name)
        obj.ua_node = await self.root_object_node.get_child(
            f"{self.namespace_index}:{name}"
        )
        await self.__init_fields(obj)

        self.objects[name] = obj
        return obj

    async def get_object(self, cls: type[T], name: str) -> T:
        if name not in self.objects:
            await self.create_object(cls, name)

        obj = self.objects[name]

        if not isinstance(obj, cls):
            raise ValueError

        return obj

    @property
    def root_object_node(self) -> Node:
        return self.client.get_objects_node()

    async def __aenter__(self) -> "OpcuaClient":
        await self.client.__aenter__()
        self.namespace_index = await self.client.get_namespace_index(
            self.server_namespace
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
