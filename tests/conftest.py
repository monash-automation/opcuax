import pytest
import pytest_asyncio

from opcuax.client import OpcuaClient
from opcuax.server import OpcuaServer

from .models import Pet, Puppy


@pytest.fixture
def endpoint() -> str:
    return "opc.tcp://localhost:44840"


@pytest.fixture
def namespace() -> str:
    return "https://github.com/monash-automation/opcuax"


@pytest_asyncio.fixture
async def server(endpoint, namespace) -> OpcuaServer:
    async with OpcuaServer(
        endpoint=endpoint,
        server_name="unittest server",
        namespace=namespace,
    ) as server:
        yield server


@pytest_asyncio.fixture
async def pet_server(server) -> OpcuaServer:
    await server.create_object_type(Pet)
    await server.create_object(Pet, "Kitty")
    await server.create_object(Puppy, "Puppy")

    yield server


@pytest_asyncio.fixture
async def client(pet_server) -> OpcuaClient:
    async with OpcuaClient(pet_server.endpoint, pet_server.namespace) as client:
        yield client
