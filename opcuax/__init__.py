import asyncio
import logging

from .main import redis_worker, run_server
from .models.printer import Printer


def config():
    return {"Printer1": Printer, "Printer2": Printer}


def server():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server(config()))


def cache():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redis_worker(config()))
