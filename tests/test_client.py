import pytest_asyncio
from opcuax.client import OpcuaClient

from .models import Pets


@pytest_asyncio.fixture
async def pets(client: OpcuaClient) -> Pets:
    yield await client.read_objects(Pets)


async def test_get_objects(client: OpcuaClient):
    pets = await client.read_objects(Pets)
    assert pets.kitty.name == ""
    assert pets.kitty.owner.name == ""


async def test_set(client: OpcuaClient, pets: Pets):
    pets.kitty.name = "foo"
    await client.update_objects(pets)

    pets = await client.read_objects(Pets)
    assert pets.kitty.name == "foo"
