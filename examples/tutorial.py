import asyncio
from typing import Annotated

from pydantic import BaseModel, Field, IPvAnyAddress, NonNegativeInt

from opcuax import (
    OpcuaClient,
    OpcuaObjects,
    OpcuaServer,
    OpcuaClientSettings,
    OpcuaServerSettings,
)

LabPos = Annotated[float, Field(ge=-200, le=200, default=0)]


class Trackable(BaseModel):
    ip: IPvAnyAddress = IPvAnyAddress("127.0.0.1")


class Position(BaseModel):
    x: LabPos
    y: LabPos


class Job(BaseModel):
    filename: str = ""
    time_used: NonNegativeInt


class Printer(Trackable):
    state: str = "Unknown"
    latest_job: Job


class Robot(Trackable):
    position: Position
    up_time: NonNegativeInt = 0


class Lab(OpcuaObjects):
    printer1: Printer
    printer2: Printer
    robot: Robot


def build_server() -> OpcuaServer:
    settings = OpcuaServerSettings(
        opcua_server_url="opc.tcp://localhost:4840",
        opcua_server_name="Opcua Lab Server",
        opcua_server_namespace="https://github.com/monash-automation/opcuax",
    )
    return OpcuaServer.from_settings(settings)


def build_client() -> OpcuaClient:
    settings = OpcuaClientSettings(
        opcua_server_url="opc.tcp://localhost:4840",
        opcua_server_namespace="https://github.com/monash-automation/opcuax",
    )
    return OpcuaClient.from_settings(settings)


async def run_server(server: OpcuaServer):
    async with server:
        await server.create_objects(Lab)

        lab = await server.read_objects(Lab)
        print(lab.model_dump_json())

        lab.robot.position = Position(x=100.0, y=100.0)
        await server.update_objects(lab)

        await server.loop()


class Printers(OpcuaObjects):
    printer1: Printer
    robot: Robot


async def run_client(client: OpcuaClient):
    await asyncio.sleep(2)  # wait until server is ready

    async with client:
        printers = await client.read_objects(Printers)
        print(printers.model_dump_json())

        printers.printer1.state = "Printing"
        printers.printer1.latest_job.filename = "A.gcode"
        await client.update_objects(printers)

        printers = await client.read_objects(Printers)
        print(printers.model_dump_json())


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_server(build_server()))
        tg.create_task(run_client(build_client()))


if __name__ == "__main__":
    asyncio.run(main())
