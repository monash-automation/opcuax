from opcuax import OpcuaServer

from tests.models import Dog


async def test_get_variable(pet_server: OpcuaServer, snoopy: Dog):
    value = await pet_server.get("Snoopy", Dog, lambda dog: dog.name)
    assert value == snoopy.name


async def test_set_variable(pet_server: OpcuaServer, snoopy: Dog):
    await pet_server.set("Snoopy", Dog, "foo", lambda dog: dog.name)
    value = await pet_server.get("Snoopy", Dog, lambda dog: dog.name)
    assert value == "foo"
