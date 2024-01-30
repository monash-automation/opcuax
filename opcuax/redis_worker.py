import asyncio
import logging

import redis.asyncio as redis

from opcuax.client import OpcuaClient, OpcuaObject
from opcuax.models import Printer
from opcuax.settings import WorkerSettings


async def main():
    logging.basicConfig(level=logging.INFO)
    settings = WorkerSettings()

    opcua_client = OpcuaClient(url=str(settings.opcua_server_url))
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
        printer1 = await opcua_client.get_object(Printer, name="Printer1")

        async with asyncio.TaskGroup() as group:
            group.create_task(cache(printer1, "printer1"))


def start():
    asyncio.run(main())
