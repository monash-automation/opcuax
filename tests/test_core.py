from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from opcuax import OpcuaModel, OpcuaServer, fetch
from pydantic import BaseModel

from tests.models import Dog, Home


@pytest.fixture
def home(snoopy: Dog) -> Home:
    return Home(name="town house", address="Greens Road", dog=snoopy)


@pytest_asyncio.fixture
async def server(
    pet_server: OpcuaServer, home: Home
) -> AsyncGenerator[OpcuaServer, None]:
    await pet_server.create("SnoopyHome", home)
    yield pet_server


@pytest.fixture
def home_proxy(server: OpcuaServer) -> Home:
    return fetch(Home, "SnoopyHome")


@pytest.fixture
def dog_proxy(server: OpcuaServer) -> Dog:
    return fetch(Dog, "Snoopy")


async def test_get(server: OpcuaServer, home_proxy: Home, home: Home) -> None:
    value = await server.read(home_proxy)
    assert value == home


async def test_get_variable(server: OpcuaServer, dog_proxy: Dog, snoopy: Dog) -> None:
    value = await server.read(dog_proxy.name)
    assert value == snoopy.name


async def test_get_nested_variable(
    server: OpcuaServer, home_proxy: Home, snoopy: Dog
) -> None:
    value = await server.read(home_proxy.dog.name)
    assert value == snoopy.name


async def test_set_variable(server: OpcuaServer, dog_proxy: Dog) -> None:
    dog_proxy.name = "foo"
    await server.commit(dog_proxy)
    value = await server.read(dog_proxy.name)
    assert value == "foo"


async def test_set_nested_variable(server: OpcuaServer, home_proxy: Home) -> None:
    home_proxy.dog.name = "foo"
    await server.commit(home_proxy)
    _home = await server.read(home_proxy)
    assert _home.dog.name == "foo"


async def test_fields_of_same_model_type(server: OpcuaServer) -> None:
    class Person(BaseModel):
        name: str

    class Model(OpcuaModel):
        mike: Person = Person(name="Mike")
        bob: Person = Person(name="Bob")
        carl: Person = Person(name="Carl")

    model_object = await server.create("model", Model())
    model: Model = await server.read(model_object)

    assert model.mike.name == "Mike"
    assert model.bob.name == "Bob"
    assert model.carl.name == "Carl"
