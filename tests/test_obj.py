import pytest_asyncio
from opcuax import OpcuaServer

from .models import Pet, Pets, Puppy


@pytest_asyncio.fixture
async def pets(pet_server: OpcuaServer) -> Pets:
    yield await pet_server.read_objects(Pets)


@pytest_asyncio.fixture
async def kitty(pets: Pets) -> Pet:
    yield pets.kitty


@pytest_asyncio.fixture
async def puppy(pets: Pets) -> Puppy:
    yield pets.puppy


async def test_get_default_value(pet_server, pets):
    pets.kitty.name = "foo"
    await pet_server.update_objects(pets)

    pets = await pet_server.read_objects(Pets)
    assert pets.kitty.name == "foo"


async def test_set_value_of_nested_object(pet_server, pets):
    pets.kitty.owner.name = "foo"
    await pet_server.update_objects(pets)

    pets = await pet_server.read_objects(Pets)
    assert pets.kitty.owner.name == "foo"


async def test_to_dict(kitty):
    data = kitty.model_dump()

    assert data == {
        "name": "",
        "age": 0,
        "weight": 0.0,
        "owner": {"name": "", "address": ""},
    }


async def test_inheritance_to_dict(puppy):
    data = puppy.model_dump()

    assert data == {
        "name": "",
        "age": 0,
        "weight": 0.0,
        "owner": {"name": "", "address": ""},
        "food": "",
        "birthday": "",
    }
