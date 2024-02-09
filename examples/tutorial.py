import asyncio
from datetime import datetime
from typing import Annotated

from opcuax import (
    OpcuaClient,
    OpcuaClientSettings,
    OpcuaModel,
    OpcuaObject,
    OpcuaServer,
    OpcuaServerSettings,
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
        obj: OpcuaObject[Printer] = await server.create(Printer(), "Printer1")
        await server.create(Printer(), "Printer2")
        await server.create(Robot(), "Robot")

        printer1: Printer = await obj.get()
        print(printer1.model_dump_json())

        printer1.state = "Ready"
        await obj.set(printer1)
        await obj.set("Ready", lambda printer: printer.state)

        filename = await obj.get(lambda printer: printer.latest_job.filename)
        job = await obj.get(lambda printer: printer.latest_job)
        assert filename == job.filename

        await server.loop()


async def run_client(client: OpcuaClient) -> None:
    await asyncio.sleep(3)  # wait until server is ready

    async with client:
        obj: OpcuaObject[Printer] = client.get_object(Printer, "Printer1")

        printer1: Printer = await obj.get()
        print(printer1.model_dump_json())

        await obj.set(
            Job(filename="A.gcode", time_used=1), lambda printer: printer.latest_job
        )


async def main() -> None:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(run_server(build_server()))
        tg.create_task(run_client(build_client()))


if __name__ == "__main__":
    asyncio.run(main())
