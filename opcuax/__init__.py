import asyncio
import logging

from opcuax.server import main


def run_server():
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
