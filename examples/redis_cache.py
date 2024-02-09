import asyncio
from inspect import isawaitable

import flatdict
import redis.asyncio as redis
from pydantic import BaseModel

from examples.client import build_client_from_settings
from examples.printer import Printer


async def redis_worker() -> None:
    opcua_client = build_client_from_settings()
    redis_client = redis.Redis(host="127.0.0.1", port=6379)

    async def cache(obj: BaseModel, key: str) -> None:
        data = flatdict.FlatDict(obj.model_dump(), delimiter=".")
        coro = redis_client.hset(key, mapping=data.as_dict())
        assert isawaitable(coro)
        await coro

    async with opcua_client, redis_client:
        printer1 = await opcua_client.get(Printer, "Printer1")
        printer2 = await opcua_client.get(Printer, "Printer2")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(cache(printer1, "Printer1"))
            tg.create_task(cache(printer2, "Printer2"))


if __name__ == "__main__":
    asyncio.run(redis_worker())
