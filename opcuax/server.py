import asyncio
import tomllib
from pathlib import Path

from asyncua import Node, Server, ua

from opcuax.builder import TypeBuilder
from opcuax.config import parse_config


async def init_server() -> Server:
    server = Server()
    await server.init()

    server.set_endpoint("opc.tcp://localhost:4840")
    server.set_server_name("MSM OPCUA Server")
    server.set_security_policy(
        [
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
        ]
    )
    await server.register_namespace("http://msm.com/server")
    return server


class ObjectCreator:
    def __init__(self, server: Server):
        self.server = server
        self.next_ns = server.get_root_node().nodeid.NamespaceIndex + 10

    async def create(self, tp: Node, name: str):
        obj = await self.server.nodes.objects.add_object(self.next_ns, name, tp.nodeid)
        self.next_ns += 1
        return obj


async def main():
    config_path = Path(__file__).parent.parent / "objects.toml"
    with open(config_path.absolute()) as f:
        config = tomllib.loads(f.read())

    template = parse_config(config)

    server = await init_server()
    type_builder = TypeBuilder(server)
    types = await type_builder.parse_types(template.types, template.base_fields)
    obj_creator = ObjectCreator(server)

    for type_name, number in template.instance_numbers.items():
        if type_name not in types:
            print(f"Cannot find type definition of {type_name}, skip")
            continue
        for i in range(number):
            await obj_creator.create(types[type_name], f"{type_name}{i+1}")

    async with server:
        while True:
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
