import asyncio
from inspect import isawaitable

import flatdict
import redis.asyncio as redis
from opcuax import OpcuaObjects
from pydantic import BaseModel

from examples.client import build_client_from_settings
from examples.printer import Printer


class Printers(OpcuaObjects):
    printer1: Printer
    printer2: Printer


async def redis_worker() -> None:
    opcua_client = build_client_from_settings()
    redis_client = redis.Redis(host="127.0.0.1", port=6379)

    async def cache(obj: BaseModel, key: str) -> None:
        data = flatdict.FlatDict(obj.model_dump(), delimiter=".")
        coro = redis_client.hset(key, mapping=data.as_dict())
        assert isawaitable(coro)
        await coro

    async with opcua_client, redis_client:
        printers = await opcua_client.read_objects(Printers)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(cache(printers.printer1, "printer1"))
            tg.create_task(cache(printers.printer1, "printer2"))


if __name__ == "__main__":
    asyncio.run(redis_worker())
