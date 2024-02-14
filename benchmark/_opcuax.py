import asyncio

from opcuax import OpcuaClient, OpcuaServer

from benchmark._config import client_settings, server_settings
from benchmark._helper import Timer, random_printer
from benchmark._models import Printer


def build_server() -> OpcuaServer:
    return OpcuaServer.from_settings(server_settings)


def build_client() -> OpcuaClient:
    return OpcuaClient.from_settings(client_settings)


async def server_read_benchmark(printers: int, n: int) -> None:
    async with build_server() as server:
        _printers = [
            await server.create(f"Printer{i+1}", Printer()) for i in range(printers)
        ]

        timer = Timer("opcuax", "server-read", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for printer in _printers:
                    tg.create_task(server.refresh(printer))

        timer.end()


async def server_write_benchmark(printers: int, n: int) -> None:
    async with build_server() as server:
        _printers = [
            await server.create(f"Printer{i+1}", Printer()) for i in range(printers)
        ]

        timer = Timer("opcuax", "server-write", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for i in range(printers):
                    tg.create_task(server.update(f"Printer{i+1}", random_printer()))

        timer.end()

        assert server.update_tasks.empty()


async def client_read_benchmark(printers: int, n: int) -> None:
    async with build_server() as server, build_client() as client:
        for i in range(printers):
            await server.create(f"Printer{i+1}", Printer())

        _printers = [
            await client.get_object(Printer, f"Printer{i+1}") for i in range(printers)
        ]

        timer = Timer("opcuax", "client-read", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for printer in _printers:
                    tg.create_task(client.refresh(printer))

        timer.end()


async def client_write_benchmark(printers: int, n: int) -> None:
    async with build_server() as server, build_client() as client:
        for i in range(printers):
            await server.create(f"Printer{i+1}", Printer())

        timer = Timer("opcuax", "client-write", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for i in range(printers):
                    tg.create_task(client.update(f"Printer{i+1}", random_printer()))

        timer.end()

        assert client.update_tasks.empty()
