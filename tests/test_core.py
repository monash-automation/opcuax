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
    await pet_server.create("SnoopyHome", home)
    yield pet_server


async def test_get_object(server: OpcuaServer, home: Home) -> None:
    _home = await server.get_object(Home, "SnoopyHome")
    assert isinstance(_home, Home)
    assert home.model_dump() == _home.model_dump()


async def test_refresh_root(server: OpcuaServer, home: Home) -> None:
    _home = await server.get_object(Home, "SnoopyHome")
    _dog = _home.dog
    _home.__dict__["name"] = "wrong"
    _home.__dict__["address"] = "wrong"
    _dog.__dict__["name"] = "wrong"
    _dog.__dict__["age"] = 999
    _dog.__dict__["weight"] = 999
    await server.refresh(_home)
    assert _home.model_dump() == home.model_dump()


async def test_refresh_part(server: OpcuaServer, home: Home) -> None:
    _home = await server.get_object(Home, "SnoopyHome")
    _dog = _home.dog
    _dog.__dict__["name"] = "wrong"
    _dog.__dict__["age"] = 999
    _dog.__dict__["weight"] = 999

    await server.refresh(_home.dog)
    assert _dog.model_dump() == home.dog.model_dump()


async def test_update_variable(server: OpcuaServer, home: Home) -> None:
    _home = await server.get_object(Home, "SnoopyHome")
    _home.name = "foo"
    _home.address = "addr"

    await server.commit()
    await server.refresh(_home)
    assert _home.name == "foo"
    assert _home.address == "addr"


async def test_update_object(server: OpcuaServer) -> None:
    _home = await server.get_object(Home, "SnoopyHome")
    dog = Dog(name="new", age=1, weight=999)
    _home.dog = dog

    await server.commit()
    await server.refresh(_home)
    assert _home.dog.model_dump() == dog.model_dump()


async def test_update_nested_variable(server: OpcuaServer) -> None:
    _home = await server.get_object(Home, "SnoopyHome")
    _home.dog.name = "foo"

    await server.commit()
    await server.refresh(_home)
    assert _home.dog.name == "foo"


async def test_update_fields_of_same_model_type(server: OpcuaServer) -> None:
    class Person(BaseModel):
        name: str

    class Model(OpcuaModel):
        mike: Person = Person(name="Mike")
        bob: Person = Person(name="Bob")
        carl: Person = Person(name="Carl")

    model = await server.create("model", Model())

    model.mike.name = "mike"
    model.bob.name = "bob"
    model.carl.name = "carl"
    await server.commit()
    await server.refresh(model)

    assert model.mike.name == "mike"
    assert model.bob.name == "bob"
    assert model.carl.name == "carl"
