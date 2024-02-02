import asyncio
import logging

import redis.asyncio as redis

from .client import OpcuaClient
from .obj import OpcuaObject
from .server import OpcuaServer
from .settings import EnvClientSettings, EnvServerSettings, WorkerSettings


async def run_server(config: dict[str, type[OpcuaObject]]):
    settings = EnvServerSettings()

    async with OpcuaServer(
        endpoint=str(settings.opcua_server_url),
        server_name=settings.opcua_server_name,
        namespace=str(settings.opcua_server_namespace),
    ) as server:
        for name, cls in config.items():
            server.logger.info("Creating OpcuaObject name=%s, type=%s", name, cls)
            obj = await server.get_object(cls, name)
        while True:
            await asyncio.sleep(settings.interval)


async def redis_worker(config: dict[str, type[OpcuaObject]]):
    settings = WorkerSettings()

    opcua_client = OpcuaClient(
        url=str(settings.opcua_server_url),
        server_namespace=str(settings.opcua_server_namespace),
    )
    redis_client = redis.Redis(
        host=settings.redis_url.host, port=settings.redis_url.port
    )

    async def cache(obj: OpcuaObject, name: str):
        while True:
            data = await obj.to_dict(flatten=True)
            logging.debug("Caching %s, %s", name, data)
            await redis_client.hset(name, mapping=data)
            await asyncio.sleep(settings.interval)

    async with opcua_client, redis_client:
        async with asyncio.TaskGroup() as group:
            for name, cls in config.items():
                obj = await opcua_client.get_object(cls, name=name)
                group.create_task(cache(obj, "printer1"))


async def run_client():
    settings = EnvClientSettings()

    async with OpcuaClient(
        url=str(settings.opcua_server_url),
        server_namespace=str(settings.opcua_server_namespace),
    ) as client:
        pass
