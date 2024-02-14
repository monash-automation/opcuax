import asyncio
from datetime import datetime
from ipaddress import IPv4Address
from typing import Annotated

from opcuax import (
    OpcuaClient,
    OpcuaClientSettings,
    OpcuaModel,
    OpcuaServer,
    OpcuaServerSettings,
)
from pydantic import BaseModel, Field, NonNegativeInt, PastDatetime

LabPos = Annotated[float, Field(ge=-200, le=200, default=0)]
UpdateTime = Annotated[datetime, PastDatetime()]


class Trackable(OpcuaModel):
    ip: IPv4Address = IPv4Address("127.0.0.1")
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
        # create() returns enhanced models that maintains corresponding node info
        printer1: Printer = await server.create("Printer1", Printer())
        printer2: Printer = await server.create("Printer2", Printer())
        await server.create("Robot", Robot())

        # Refresh object values
        await server.refresh(printer1)
        print(printer1.model_dump_json())

        # Refresh an inner object
        await server.refresh(printer2.latest_job)

        printer1.state = "Printing"
        printer1.latest_job.filename = "A.gcode"
        # submit changes to the server
        await server.commit()

        # WARNING: printer1 = Printer() won't update all nodes in printer1
        # instead the variable "printer1" is points to the new Printer instance
        await server.update("Printer1", Printer())

        await server.loop()


async def run_client(client: OpcuaClient) -> None:
    # wait until server is ready if you run server and client in one program
    await asyncio.sleep(3)

    async with client:
        # Get an object from the server
        printer = await client.get_object(Printer, "Printer1")
        print(printer.model_dump_json())

        printer.latest_job.time_used += 10
        printer.state = "Finished"
        await client.commit()

        await client.refresh(printer)


async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_server(build_server()))
        tg.create_task(run_client(build_client()))


if __name__ == "__main__":
    asyncio.run(main())
