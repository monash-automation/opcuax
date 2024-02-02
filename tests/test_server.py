from .models import Home, Pet, Puppy


async def test_create_object_type(server):
    type_node = await server.create_object_type(Pet)

    name = await type_node.get_child("2:Name")
    owner = await type_node.get_child("2:Owner")
    owner_name = await type_node.get_child("2:Owner/2:Name")

    assert all([name, owner, owner_name])


async def test_inheritance(server):
    type_node = await server.create_object_type(Puppy)

    name = await type_node.get_child("2:Name")
    food = await type_node.get_child("2:Food")
    birthday = await type_node.get_child("2:BirthDay")

    assert all([name, food, birthday])


async def test_fields_of_same_type(server):
    type_node = await server.create_object_type(Home)

    dog1 = await type_node.get_child("2:Dog1")
    dog2 = await type_node.get_child("2:Dog2")

    assert all([dog1, dog2])
    assert dog1.nodeid != dog2.nodeid


async def test_create_object(server):
    await server.create_object_type(Pet)
    pet = await server.create_object(Pet, "Kitty")

    name = await server.root_object_node.get_child("2:Kitty/2:Name")

    assert name.nodeid == pet.name.ua_node.nodeid


async def test_create_object_without_creating_type(server):
    await server.create_object(Pet, "Kitty")

    assert Pet in server.object_type_nodes
