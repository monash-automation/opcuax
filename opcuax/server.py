import asyncio
from types import TracebackType

from asyncua import Node, Server, ua
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from .core import Opcuax, _OpcuaObjects
from .node import OpcuaObjNode
from .settings import EnvOpcuaServerSettings, OpcuaServerSettings
from .values import opcua_default_value


class OpcuaServer(Opcuax):
    interval: float
    server: Server
    ua_object_type_node: Node
    object_type_nodes: dict[type[BaseModel], Node]

    def __init__(
        self, endpoint: str, name: str, namespace: str, interval: float = 1
    ) -> None:
        super().__init__(endpoint, namespace)
        self.interval = interval
        self.object_type_nodes = {}

        self.server = Server()
        self.server.set_endpoint(endpoint)
        self.server.set_server_name(name)
        self.server.set_security_policy(
            [
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign,
            ]
        )

    @staticmethod
    def from_settings(settings: OpcuaServerSettings) -> "OpcuaServer":
        return OpcuaServer(
            endpoint=str(settings.opcua_server_url),
            name=settings.opcua_server_name,
            namespace=str(settings.opcua_server_namespace),
            interval=settings.opcua_server_interval,
        )

    @staticmethod
    def from_env(env_file: str = ".env") -> "OpcuaServer":
        settings = EnvOpcuaServerSettings(_env_file=env_file)
        return OpcuaServer.from_settings(settings)

    async def loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval)

    async def __add_variable(self, parent: Node, name: str, field: FieldInfo) -> Node:
        value = opcua_default_value(field)
        assert field.annotation is not None

        if issubclass(field.annotation, float):
            var = await parent.add_variable(
                self.namespace, name, value, varianttype=ua.VariantType.Float
            )
        else:
            var = await parent.add_variable(self.namespace, name, value)
        await var.set_modelling_rule(True)
        await var.set_writable(True)
        return var

    async def __add_object(self, parent: Node, name: str) -> Node:
        node = await parent.add_object(self.namespace, name)
        await node.set_modelling_rule(True)
        return node

    async def create_ua_object_type(self, model_cls: type[BaseModel]) -> Node:
        if model_cls in self.object_type_nodes:
            return self.object_type_nodes[model_cls]

        async def dfs(cls: type[BaseModel], parent: Node) -> None:
            for name, field in cls.model_fields.items():
                field_cls = field.annotation
                assert field_cls is not None

                if issubclass(field_cls, BaseModel):
                    # nested types are not supported
                    node = await self.__add_object(parent, name)
                    await dfs(field_cls, node)
                else:
                    await self.__add_variable(parent, name, field)

        type_node = await self.ua_object_type_node.add_object_type(
            self.namespace, model_cls.__name__
        )
        await dfs(model_cls, type_node)

        self.object_type_nodes[model_cls] = type_node
        return type_node

    async def create_ua_object(self, cls: type[BaseModel], name: str) -> None:
        if cls not in self.object_type_nodes:
            await self.create_ua_object_type(cls)

        await self.ua_objects_node.add_object(
            self.namespace, name, objecttype=self.object_type_nodes[cls].nodeid
        )

    async def create_ua_objects(self, cls: type[_OpcuaObjects]) -> None:
        for name, field in cls.model_fields.items():
            field_cls = field.annotation
            assert field_cls is not None

            if issubclass(field_cls, BaseModel):
                await self.create_ua_object(field_cls, name)
            else:
                await self.__add_variable(self.objects_node.ua_node, name, field)

    async def create_objects(self, cls: type[_OpcuaObjects]) -> None:
        await self.create_ua_objects(cls)
        await self.create_opcua_nodes(cls)

    async def __aenter__(self) -> "OpcuaServer":
        await self.server.init()
        self.namespace = await self.server.register_namespace(self.namespace_uri)
        self.ua_objects_node = self.server.nodes.objects
        self.ua_object_type_node = self.server.nodes.base_object_type
        self.objects_node = OpcuaObjNode("Objects", self.ua_objects_node, 0)
        await self.server.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.server.__aexit__(exc_type, exc_val, exc_tb)
