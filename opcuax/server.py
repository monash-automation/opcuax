import logging
from logging import Logger
from types import TracebackType
from typing import TypeVar

from asyncua import Node, Server, ua

from .obj import OpcuaObject
from .var import OpcuaVariable

T = TypeVar("T", bound=OpcuaObject)


class OpcuaServer:
    endpoint: str
    namespace: str
    namespace_index: int
    server: Server
    object_type_nodes: dict[type[OpcuaObject], Node]
    objects: dict[str, OpcuaObject]
    logger: Logger

    def __init__(self, endpoint: str, server_name: str, namespace: str) -> None:
        self.object_type_nodes = {}
        self.objects = {}
        self.server = Server()
        self.endpoint = endpoint
        self.namespace = namespace
        self.server.set_endpoint(endpoint)
        self.server.set_server_name(server_name)
        self.server.set_security_policy(
            [
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign,
            ]
        )
        self.logger = logging.getLogger(type(self).__name__)

    async def add_variable(self, parent: Node, var: OpcuaVariable) -> Node:
        var = await parent.add_variable(self.namespace_index, var.ua_name, var.default)
        await var.set_modelling_rule(True)
        await var.set_writable(True)
        return var

    async def add_object(self, parent: Node, obj: OpcuaObject) -> Node:
        node = await parent.add_object(self.namespace_index, obj.ua_name)
        await node.set_modelling_rule(True)
        return node

    async def create_object_type(self, object_type: type[OpcuaObject]) -> Node:
        if object_type in self.object_type_nodes:
            return self.object_type_nodes[object_type]

        async def dfs(cls: type[OpcuaObject], parent: Node) -> None:
            for field in cls.opcua_class_vars().values():
                match field:
                    case OpcuaVariable() as var:
                        await self.add_variable(parent, var)
                    case OpcuaObject() as obj:
                        # nested types are not supported
                        node = await self.add_object(parent, obj)
                        await dfs(type(obj), node)

        type_node = await self.root_type_node.add_object_type(
            self.namespace_index, object_type.__name__
        )
        self.object_type_nodes[object_type] = type_node

        await dfs(object_type, type_node)
        return type_node

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
        if cls not in self.object_type_nodes.values():
            await self.create_object_type(cls)

        obj = cls(name)
        obj.ua_node = await self.root_object_node.add_object(
            self.namespace_index, name, objecttype=self.object_type_nodes[cls].nodeid
        )
        await self.__init_fields(obj)

        self.objects[name] = obj
        return obj

    async def get_object(self, cls: type[T], name: str) -> T:
        if name not in self.objects:
            await self.create_object(cls, name)

        obj = self.objects[name]

        if not isinstance(obj, cls):
            raise ValueError(f"{name} is already used for an {cls} instance")

        return obj

    @property
    def root_object_node(self) -> Node:
        return self.server.nodes.objects

    @property
    def root_type_node(self) -> Node:
        return self.server.nodes.base_object_type

    async def __aenter__(self) -> "OpcuaServer":
        await self.server.init()
        self.namespace_index = await self.server.register_namespace(self.namespace)
        await self.server.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.server.__aexit__(exc_type, exc_val, exc_tb)
