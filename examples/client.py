import asyncio
import logging

from examples.printer import Printer, PrinterHead
from opcuax import OpcuaClient, OpcuaObjects, OpcuaClientSettings


class Desk(OpcuaObjects):
    printer1: Printer


def build_client_from_settings() -> OpcuaClient:
    settings = OpcuaClientSettings(
        opcua_server_url="opc.tcp://localhost:4840",
        opcua_server_namespace="https://github.com/monash-automation/opcuax",
    )
    return OpcuaClient.from_settings(settings)


def build_client_from_env() -> OpcuaClient:
    return OpcuaClient.from_env(env_file=".env")


async def run_client() -> None:
    client = build_client_from_settings()

    async with client:
        # read object values
        desk = await client.read_objects(Desk)
        print(desk.model_dump_json())

        # update object values
        desk.printer1.head = PrinterHead(x=5, y=10, z=15)
        await client.update_objects(desk)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_client())
