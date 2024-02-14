import asyncio
from inspect import isawaitable

import flatdict
import redis.asyncio as redis
from opcuax import OpcuaClient, OpcuaModel


class _Printer(OpcuaModel):
    state: str


async def redis_worker(opcua_client: OpcuaClient) -> None:
    redis_client = redis.Redis(host="127.0.0.1", port=6379)

    async def cache(printer: _Printer, key: str) -> None:
        data = flatdict.FlatDict(printer.model_dump(), delimiter=".")
        coro = redis_client.hset(key, mapping=data.as_dict())
        assert isawaitable(coro)
        await coro

    async with opcua_client, redis_client:
        printer1 = await opcua_client.get_object(_Printer, "Printer1")
        printer2 = await opcua_client.get_object(_Printer, "Printer2")

        await opcua_client.refresh(printer1)
        await opcua_client.refresh(printer2)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(cache(printer1, "Printer1"))
            tg.create_task(cache(printer2, "Printer2"))
