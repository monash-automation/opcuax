from opcuax import OpcuaServer

from .models import Home, Pet, Pets, Puppy


async def test_create_object_type(server: OpcuaServer) -> None:
    type_node = await server.create_ua_object_type(Pet)

    name = await type_node.get_child("2:name")
    owner = await type_node.get_child("2:owner")
    owner_name = await type_node.get_child("2:owner/2:name")

    assert all([name, owner, owner_name])


async def test_inheritance(server: OpcuaServer) -> None:
    type_node = await server.create_ua_object_type(Puppy)

    name = await type_node.get_child("2:name")
    food = await type_node.get_child("2:food")
    birthday = await type_node.get_child("2:birthday")

    assert all([name, food, birthday])


async def test_fields_of_same_type(server: OpcuaServer) -> None:
    type_node = await server.create_ua_object_type(Home)

    dog1 = await type_node.get_child("2:dog1")
    dog2 = await type_node.get_child("2:dog2")

    assert all([dog1, dog2])
    assert dog1.nodeid != dog2.nodeid


async def test_read_objects(pet_server: OpcuaServer) -> None:
    pets = await pet_server.read_objects(Pets)

    assert pets.kitty.name == ""
    assert pets.kitty.owner.name == ""
