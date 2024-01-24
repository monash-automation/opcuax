import asyncio
import tomllib
from pathlib import Path

from asyncua import Server, ua
from asyncua.common.instantiate_util import instantiate

from opcuax.config import parse_config
from opcuax.custom_types import create_object_types


class OpcuaServer(Server):
    index: int | None = None
    namespace: str = "http://monashautomation.com/server"
    server_name: str = "Monash Automation OPC UA Server"

    def __init__(self, endpoint: str = "opc.tcp://localhost:4840"):
        super().__init__()
        self.set_endpoint(endpoint)
        self.set_server_name(self.server_name)
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
    config_path = Path(__file__).parent.parent / "objects.toml"
    with open(config_path.absolute()) as f:
        config = tomllib.loads(f.read())

    template = parse_config(config)

    async with OpcuaServer() as server:
        obj_types = await create_object_types(
            server.nodes.base_object_type, template.types, template.base_fields
        )

        for type_name, number in template.instance_numbers.items():
            if type_name not in obj_types:
                print(f"Cannot find type definition of {type_name}, skip")
                continue
            for i in range(number):
                await instantiate(
                    server.nodes.objects,
                    obj_types[type_name],
                    bname=f"{type_name}{i+1}",
                )
        while True:
            await asyncio.sleep(0.1)
