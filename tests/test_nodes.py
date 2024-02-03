from opcuax.node import OpcuaObjNode
from tests.models import Pets


async def test_server_create_nodes(pet_server):
    await pet_server.create_opcua_nodes(Pets)

    objects = pet_server.objects_node

    ua_kitty = await pet_server.ua_objects_node.get_child("2:kitty")
    ua_puppy = await pet_server.ua_objects_node.get_child("2:puppy")

    assert objects.children["kitty"].ua_node.nodeid == ua_kitty.nodeid
    assert objects.children["puppy"].ua_node.nodeid == ua_puppy.nodeid


async def test_to_dict(pet_server):
    await pet_server.create_opcua_nodes(Pets)

    kitty_node = pet_server.objects_node.children["kitty"]

    assert isinstance(kitty_node, OpcuaObjNode)

    data = await kitty_node.to_dict()

    assert data == {
        "name": "",
        "age": 0,
        "weight": 0.0,
        "owner": {"name": "", "address": ""},
    }
