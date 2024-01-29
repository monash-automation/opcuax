import asyncio
import logging
import tomllib

from asyncua import Node, Server, ua
from asyncua.common.instantiate_util import instantiate

from opcuax.config import parse_config
from opcuax.custom_types import create_object_types
from opcuax.settings import EnvServerSettings


class OpcuaServer(Server):
    index: int
    namespace: str

    def __init__(self, server_name: str, endpoint: str, namespace: str):
        super().__init__()
        self.namespace = namespace
        self.set_endpoint(endpoint)
        self.set_server_name(server_name)
        self.set_security_policy(
            [
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                ua.SecurityPolicyType.Basic256Sha256_Sign,
            ]
        )

    async def __aenter__(self):
        await self.init()
        self.index = await self.register_namespace(self.namespace)
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)


async def main():
    settings = EnvServerSettings()

    logging.info(
        "Load OPC UA object metadata from %s", settings.metadata_file.absolute()
    )

    with open(settings.metadata_file.absolute()) as f:
        config = tomllib.loads(f.read())

    template = parse_config(config)

    async with OpcuaServer(
        endpoint=str(settings.opcua_server_url),
        server_name=settings.opcua_server_name,
        namespace=str(settings.opcua_server_namespace),
    ) as server:
        obj_types = await create_object_types(
            server.nodes.base_object_type, template.types, template.base_fields
        )

        for type_name, number in template.instance_numbers.items():
            if type_name not in obj_types:
                logging.warning("Cannot find type definition of %s, skip", type_name)
                continue
            for i in range(number):
                obj_name = f"{type_name}{i+1}"
                nodes = await instantiate(
                    server.nodes.objects,
                    obj_types[type_name],
                    bname=obj_name,
                )
                obj_node: Node = nodes[0]
                logging.info("Created OPC UA object %s, name = %s", obj_node, obj_name)

        while True:
            await asyncio.sleep(settings.interval)
