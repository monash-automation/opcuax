import pytest_asyncio

from opcuax.client import OpcuaClient

from .models import Pet, PetOwner, Puppy


@pytest_asyncio.fixture
async def kitty(client: OpcuaClient) -> Pet:
    return await client.get_object(Pet, "Kitty")


@pytest_asyncio.fixture
async def puppy(client: OpcuaClient) -> Puppy:
    return await client.get_object(Puppy, "Puppy")


async def test_get_object(client: OpcuaClient):
    pet = await client.get_object(Pet, "Kitty")
    puppy = await client.get_object(Puppy, "Puppy")
    assert pet is not None
    assert puppy is not None


async def test_get(kitty: Pet):
    name = await kitty.name.get()
    assert name == Pet.name.default


async def test_set(kitty: Pet):
    await kitty.name.set("foo")
    name = await kitty.name.get()
    assert name == "foo"


async def test_get_from_nested_object(kitty: Pet):
    owner_name = await kitty.owner.name.get()
    assert owner_name == PetOwner.name.default


async def test_set_value_of_nested_object(kitty: Pet):
    await kitty.owner.name.set("foo")
    owner_name = await kitty.owner.name.get()
    assert owner_name == "foo"
