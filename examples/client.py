import asyncio
import logging

from opcuax import OpcuaClient, OpcuaClientSettings, OpcuaObjects

from examples.printer import Printer, PrinterHead


class Desk(OpcuaObjects):
    printer1: Printer


def build_client_from_settings() -> OpcuaClient:
    settings = OpcuaClientSettings(
        opcua_server_url="opc.tcp://localhost:4840",
        opcua_server_namespace="https://github.com/monash-automation/opcuax",
    )
    return OpcuaClient.from_settings(settings)


def build_client_from_env() -> OpcuaClient:
    return OpcuaClient.from_env(env_file=".env")


async def run_client() -> None:
    client = build_client_from_settings()

    async with client:
        # read object values
        printer1 = await client.get(Printer, "Printer1")
        print(printer1.model_dump_json())

        # update a field
        await client.set(
            Printer,
            "Printer1",
            PrinterHead(x=5, y=10, z=15),
            lambda printer: printer.head,
        )

        # update all fields
        await client.set(Printer, "Printer1", printer1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_client())
