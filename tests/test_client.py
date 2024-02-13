from datetime import datetime
from typing import Annotated

from opcuax import OpcuaModel, OpcuaServer
from opcuax.client import OpcuaClient
from pydantic import Field, PastDatetime

from .models import Dog


async def test_read_snoopy(client: OpcuaClient, snoopy: Dog) -> None:
    dog = await client.get_object(Dog, "Snoopy")
    assert dog.model_dump() == snoopy.model_dump()


async def test_read_field(client: OpcuaClient, snoopy: Dog) -> None:
    dog = await client.get_object(Dog, "Snoopy")
    assert dog.name == snoopy.name


async def test_datetime(server: OpcuaServer, client: OpcuaClient) -> None:
    class Model(OpcuaModel):
        val: Annotated[datetime, PastDatetime(), Field(default_factory=datetime.now)]

    model = await server.create("model", Model())

    assert model.val < datetime.now()
