from collections.abc import AsyncGenerator

import pytest_asyncio
from opcuax.client import OpcuaClient

from .models import Pets


@pytest_asyncio.fixture
async def pets(client: OpcuaClient) -> AsyncGenerator[Pets, None]:
    yield await client.read_objects(Pets)


async def test_get_objects(client: OpcuaClient) -> None:
    pets = await client.read_objects(Pets)
    assert pets.kitty.name == ""
    assert pets.kitty.owner.name == ""


async def test_set(client: OpcuaClient, pets: Pets) -> None:
    pets.kitty.name = "foo"
    await client.update_objects(pets)

    pets = await client.read_objects(Pets)
    assert pets.kitty.name == "foo"
