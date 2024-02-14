import asyncio
import logging

from benchmark import _asyncua, _opcuax

server_read_cases = [(10, 10), (10, 100), (10, 1000), (10, 5000)]
client_read_cases = [(10, 10), (10, 100), (10, 500), (10, 1000)]
write_cases = [(10, 10), (10, 100), (10, 250), (10, 500)]


async def main() -> None:
    for printers, reads in server_read_cases:
        await _opcuax.server_read_benchmark(printers, reads)
        await _asyncua.server_read_benchmark(printers, reads)

    for printers, reads in client_read_cases:
        await _opcuax.client_read_benchmark(printers, reads)
        await _asyncua.client_read_benchmark(printers, reads)

    for printers, writes in write_cases:
        await _opcuax.server_write_benchmark(printers, writes)
        await _asyncua.server_write_benchmark(printers, writes)

    for printers, writes in write_cases:
        await _opcuax.client_write_benchmark(printers, writes)
        await _asyncua.client_write_benchmark(printers, writes)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    asyncio.run(main())
