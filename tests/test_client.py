from datetime import datetime
from typing import Annotated

from opcuax import OpcuaModel, OpcuaServer, fetch
from opcuax.client import OpcuaClient
from pydantic import Field, PastDatetime

from .models import Dog


async def test_read_snoopy(client: OpcuaClient, snoopy: Dog) -> None:
    proxy = fetch(Dog, "Snoopy")
    dog = await client.read(proxy)
    assert dog == snoopy


async def test_read_field(client: OpcuaClient, snoopy: Dog) -> None:
    proxy = fetch(Dog, "Snoopy")
    name = await client.read(proxy.name)
    assert name == snoopy.name


async def test_datetime(server: OpcuaServer, client: OpcuaClient) -> None:
    class Model(OpcuaModel):
        val: Annotated[datetime, PastDatetime(), Field(default_factory=datetime.now)]

    proxy = await server.create("model", Model())

    model = await client.read(proxy)
    assert model.val < datetime.now()
