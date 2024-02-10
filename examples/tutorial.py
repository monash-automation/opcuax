import asyncio
from datetime import datetime
from typing import Annotated

from opcuax import (
    OpcuaClient,
    OpcuaClientSettings,
    OpcuaModel,
    OpcuaServer,
    OpcuaServerSettings,
    fetch,
)
from pydantic import BaseModel, Field, IPvAnyAddress, NonNegativeInt, PastDatetime

LabPos = Annotated[float, Field(ge=-200, le=200, default=0)]
UpdateTime = Annotated[datetime, PastDatetime()]


class Trackable(OpcuaModel):
    ip: IPvAnyAddress = "127.0.0.1"
    last_update: UpdateTime = Field(default_factory=datetime.now)


class Position(BaseModel):
    x: LabPos = 0
    y: LabPos = 0


class Job(BaseModel):
    filename: str = ""
    time_used: NonNegativeInt = 0


class Printer(Trackable):
    state: str = "Unknown"
    latest_job: Job = Job()


class Robot(Trackable):
    position: Position = Position()
    up_time: NonNegativeInt = 0


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


async def run_server(server: OpcuaServer) -> None:
    async with server:
        proxy: Printer = await server.create(Printer(), "Printer1")
        await server.create(Printer(), "Printer2")
        await server.create(Robot(), "Robot")

        # Read all nodes
        printer1: Printer = await server.read(proxy)
        print(printer1.model_dump_json())

        # Read a subset of nodes
        job = await server.read(proxy.latest_job)
        assert printer1.latest_job == job

        # The proxy object records all changes
        proxy.latest_job.filename = "A.gcode"
        # sync changes to server
        await server.commit(proxy)

        # WARNING: proxy = printer1 won't update all nodes to printer1
        # instead the variable "proxy" is reference to printer1
        # Please use the update function to update all nodes from a model
        await server.update("Printer2", printer1)

        await server.loop()


async def run_client(client: OpcuaClient) -> None:
    await asyncio.sleep(3)  # wait until server is ready

    async with client:
        proxy = fetch(Printer, "Printer1")

        printer: Printer = await client.read(proxy)
        print(printer.model_dump_json())

        proxy.latest_job = Job(filename="A.gcode", time_used=1)
        await client.commit(proxy)


async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_server(build_server()))
        tg.create_task(run_client(build_client()))


if __name__ == "__main__":
    asyncio.run(main())
