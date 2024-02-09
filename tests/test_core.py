from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from opcuax import OpcuaModel, OpcuaObject, OpcuaServer
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


@pytest.fixture
def home_object(server: OpcuaServer) -> OpcuaObject[Home]:
    return server.get_object(Home, "SnoopyHome")


@pytest.fixture
def dog_object(server: OpcuaServer) -> OpcuaObject[Dog]:
    return server.get_object(Dog, "Snoopy")


async def test_get(home_object: OpcuaObject[Home], home: Home) -> None:
    value = await home_object.get()
    assert value == home


async def test_get_variable(dog_object: OpcuaObject[Dog], snoopy: Dog) -> None:
    value = await dog_object.get(lambda dog: dog.name)
    assert value == snoopy.name


async def test_get_nested_variable(home_object: OpcuaObject[Home], snoopy: Dog) -> None:
    value = await home_object.get(lambda _home: _home.dog.name)
    assert value == snoopy.name


async def test_set_variable(dog_object: OpcuaObject[Dog]) -> None:
    await dog_object.set("foo", lambda dog: dog.name)
    value = await dog_object.get(lambda dog: dog.name)
    assert value == "foo"


async def test_set_nested_variable(home_object: OpcuaObject[Home]) -> None:
    await home_object.set("foo", lambda _home: _home.dog.name)
    _home = await home_object.get()
    assert _home.dog.name == "foo"


async def test_fields_of_same_model_type(server: OpcuaServer) -> None:
    class Person(BaseModel):
        name: str

    class Model(OpcuaModel):
        mike: Person = Person(name="Mike")
        bob: Person = Person(name="Bob")
        carl: Person = Person(name="Carl")

    model_object = await server.create(Model(), "model")
    model: Model = await model_object.get()

    assert model.mike.name == "Mike"
    assert model.bob.name == "Bob"
    assert model.carl.name == "Carl"
