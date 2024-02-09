from opcuax import OpcuaServer

from .models import Home


async def test_create_object_type(server: OpcuaServer) -> None:
    type_node = await server.create_ua_object_type(Home)

    name = await type_node.get_child("2:name")
    owner = await type_node.get_child("2:address")
    dog_name = await type_node.get_child("2:dog/2:name")

    assert all([name, owner, dog_name])
