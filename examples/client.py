import asyncio
import logging

from opcuax import OpcuaClient, OpcuaClientSettings, OpcuaObject

from examples.printer import Printer, PrinterHead


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
        obj: OpcuaObject[Printer] = client.get_object(Printer, "Printer1")

        printer1 = await obj.get()
        print(printer1.model_dump_json())

        # update a field
        await obj.set(PrinterHead(x=5, y=10, z=15), lambda printer: printer.head)

        # update all fields
        await obj.set(printer1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_client())
