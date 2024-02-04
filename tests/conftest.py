from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from opcuax import OpcuaClient, OpcuaServer

from .models import Pets


@pytest.fixture
def endpoint() -> str:
    return "opc.tcp://localhost:44840"


@pytest.fixture
def namespace() -> str:
    return "https://github.com/monash-automation/opcuax"


@pytest_asyncio.fixture
async def server(endpoint: str, namespace: str) -> AsyncGenerator[OpcuaServer, None]:
    async with OpcuaServer(
        endpoint=endpoint,
        name="unittest server",
        namespace=namespace,
    ) as server:
        yield server


@pytest_asyncio.fixture
async def pet_server(server: OpcuaServer) -> AsyncGenerator[OpcuaServer, None]:
    await server.create_objects(Pets)

    yield server


@pytest_asyncio.fixture
async def client(pet_server: OpcuaServer) -> AsyncGenerator[OpcuaClient, None]:
    async with OpcuaClient(pet_server.endpoint, pet_server.namespace_uri) as client:
        yield client
