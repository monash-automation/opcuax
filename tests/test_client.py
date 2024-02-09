from datetime import datetime
from typing import Annotated

from opcuax import OpcuaModel, OpcuaServer
from opcuax.client import OpcuaClient
from pydantic import Field, PastDatetime

from .models import Dog


async def test_read_snoopy(client: OpcuaClient, snoopy: Dog) -> None:
    dog = await client.get(Dog, "Snoopy")
    assert dog == snoopy


async def test_read_field(client: OpcuaClient, snoopy: Dog) -> None:
    name = await client.get(Dog, "Snoopy", lambda dog: dog.name)
    assert name == snoopy.name


async def test_datetime(server: OpcuaServer, client: OpcuaClient) -> None:
    class Model(OpcuaModel):
        val: Annotated[datetime, PastDatetime(), Field(default_factory=datetime.now)]

    await server.create(Model(), "model")

    model = await client.get(Model, "model")
    assert model.val < datetime.now()
