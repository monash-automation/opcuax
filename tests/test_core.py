from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from opcuax import OpcuaModel, OpcuaServer
from pydantic import BaseModel

from tests.models import Dog, Home


@pytest.fixture
def home(snoopy: Dog) -> Home:
    return Home(name="town house", address="Greens Road", dog=snoopy)


@pytest_asyncio.fixture
async def server(
    pet_server: OpcuaServer, home: Home
) -> AsyncGenerator[OpcuaServer, None]:
    await pet_server.create(home, name="SnoopyHome")
    yield pet_server


async def test_get(server: OpcuaServer, home: Home) -> None:
    value = await server.get(Home, "SnoopyHome")
    assert value == home


async def test_get_variable(server: OpcuaServer, snoopy: Dog) -> None:
    value = await server.get(Dog, "Snoopy", lambda dog: dog.name)
    assert value == snoopy.name


async def test_get_nested_variable(server: OpcuaServer, snoopy: Dog) -> None:
    value = await server.get(Home, "SnoopyHome", lambda _home: _home.dog.name)
    assert value == snoopy.name


async def test_set_variable(server: OpcuaServer) -> None:
    await server.set(Dog, "Snoopy", "foo", lambda dog: dog.name)
    value = await server.get(Dog, "Snoopy", lambda dog: dog.name)
    assert value == "foo"


async def test_set_nested_variable(server: OpcuaServer) -> None:
    await server.set(Home, "SnoopyHome", "foo", lambda _home: _home.dog.name)
    _home = await server.get(Home, "SnoopyHome")
    assert _home.dog.name == "foo"


async def test_fields_of_same_model_type(server: OpcuaServer) -> None:
    class Person(BaseModel):
        name: str

    class Model(OpcuaModel):
        mike: Person = Person(name="Mike")
        bob: Person = Person(name="Bob")
        carl: Person = Person(name="Carl")

    await server.create(Model(), "model")
    model: Model = await server.get(Model, "model")

    assert model.mike.name == "Mike"
    assert model.bob.name == "Bob"
    assert model.carl.name == "Carl"
