import asyncio
import logging

from examples.printer import Printer, Temperature
from opcuax import OpcuaObjects, OpcuaServer
from opcuax.settings import OpcuaServerSettings


# objects we want to create in the OPC UA server
# Please note the class must extend OpcuaObjects
class Lab(OpcuaObjects):
    printer1: Printer
    printer2: Printer
    printer3: Printer


def build_server_from_settings() -> OpcuaServer:
    settings = OpcuaServerSettings(
        opcua_server_url="opc.tcp://localhost:4840",
        opcua_server_name="Opcua Lab Server",
        opcua_server_namespace="https://github.com/monash-automation/opcuax",
    )
    return OpcuaServer.from_settings(settings)


def build_server_from_env() -> OpcuaServer:
    return OpcuaServer.from_env(env_file=".env")


async def run_server():
    server = build_server_from_settings()

    async with server:
        # Create objects under node "0:Objects"
        await server.create_objects(Lab)

        # Read current values of all objects
        printers = await server.read_objects(Lab)
        print(printers.model_dump_json())

        # Update object values
        printers.printer1.state = "Ready"
        printers.printer1.bed = Temperature(actual=45.5, target=100)
        await server.update_objects(printers)

        await server.loop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server())
