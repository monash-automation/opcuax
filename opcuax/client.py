from types import TracebackType

from asyncua import Client

from .core import Opcuax
from .node import OpcuaObjNode
from .settings import EnvOpcuaClientSettings, OpcuaClientSettings


class OpcuaClient(Opcuax):
    client: Client
    server_namespace: str

    def __init__(self, endpoint: str, namespace: str):
        super().__init__(endpoint, namespace)
        self.client: Client = Client(endpoint)

    @staticmethod
    def from_settings(settings: OpcuaClientSettings) -> "OpcuaClient":
        return OpcuaClient(
            endpoint=str(settings.opcua_server_url),
            namespace=str(settings.opcua_server_namespace),
        )

    @staticmethod
    def from_env(env_file: str = ".env") -> "OpcuaClient":
        settings = EnvOpcuaClientSettings(_env_file=env_file)
        return OpcuaClient.from_settings(settings)

    async def __aenter__(self) -> "OpcuaClient":
        await self.client.__aenter__()
        self.namespace = await self.client.get_namespace_index(self.namespace_uri)
        self.ua_objects_node = self.client.get_objects_node()
        self.objects_node = OpcuaObjNode("Objects", self.ua_objects_node, 0)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
