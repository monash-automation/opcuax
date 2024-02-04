from collections.abc import AsyncGenerator

import pytest_asyncio
from opcuax import OpcuaServer

from .models import Pet, Pets, Puppy


@pytest_asyncio.fixture
async def pets(pet_server: OpcuaServer) -> AsyncGenerator[Pets, None]:
    yield await pet_server.read_objects(Pets)


@pytest_asyncio.fixture
async def kitty(pets: Pets) -> AsyncGenerator[Pet, None]:
    yield pets.kitty


@pytest_asyncio.fixture
async def puppy(pets: Pets) -> AsyncGenerator[Puppy, None]:
    yield pets.puppy


async def test_get_default_value(pet_server: OpcuaServer, pets: Pets) -> None:
    pets.kitty.name = "foo"
    await pet_server.update_objects(pets)

    pets = await pet_server.read_objects(Pets)
    assert pets.kitty.name == "foo"


async def test_set_value_of_nested_object(pet_server: OpcuaServer, pets: Pets) -> None:
    pets.kitty.owner.name = "foo"
    await pet_server.update_objects(pets)

    pets = await pet_server.read_objects(Pets)
    assert pets.kitty.owner.name == "foo"


async def test_to_dict(kitty: Pets) -> None:
    data = kitty.model_dump()

    assert data == {
        "name": "",
        "age": 0,
        "weight": 0.0,
        "owner": {"name": "", "address": ""},
    }


async def test_inheritance_to_dict(puppy: Puppy) -> None:
    data = puppy.model_dump()

    assert data == {
        "name": "",
        "age": 0,
        "weight": 0.0,
        "owner": {"name": "", "address": ""},
        "food": "",
        "birthday": "",
    }
