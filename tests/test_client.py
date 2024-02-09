from opcuax.client import OpcuaClient

from .models import Dog


async def test_read_snoopy(client: OpcuaClient, snoopy: Dog) -> None:
    dog = await client.get(Dog, "Snoopy")
    assert dog == snoopy


async def test_read_field(client: OpcuaClient, snoopy: Dog) -> None:
    name = await client.get(Dog, "Snoopy", lambda dog: dog.name)
    assert name == snoopy.name
