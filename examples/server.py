import asyncio
import logging

from opcuax import OpcuaServer, OpcuaServerSettings

from examples.printer import Printer, Temperature


def build_server_from_settings() -> OpcuaServer:
    settings = OpcuaServerSettings(
        opcua_server_url="opc.tcp://localhost:4840",
        opcua_server_name="Opcua Lab Server",
        opcua_server_namespace="https://github.com/monash-automation/opcuax",
    )
    return OpcuaServer.from_settings(settings)


def build_server_from_env() -> OpcuaServer:
    return OpcuaServer.from_env(env_file=".env")


async def run_server() -> None:
    server = build_server_from_settings()

    async with server:
        # Create objects under node "0:Objects"
        await server.create(Printer(), "Printer1")
        await server.create(Printer(), "Printer2")
        await server.create(Printer(), "Printer3")

        # Read an object
        printer1: Printer = await server.get(Printer, "Printer1")
        print(f"Printer1: {printer1.model_dump()}")

        # Read a certain field
        job_file: str = await server.get(
            Printer, "Printer1", lambda printer: printer.job.file
        )
        bed_temp: Temperature = await server.get(
            Printer, "Printer1", lambda printer: printer.bed
        )
        print(f"job file: {job_file}, bed temperature: {bed_temp.model_dump()}")

        # Update all fields
        printer1.state = "Printing"
        printer1.nozzle = Temperature(actual=20, target=100)
        await server.set(Printer, "Printer1", printer1)

        # Update a certain field
        await server.set(Printer, "Printer1", "Ready", lambda printer: printer.state)
        await server.set(
            Printer,
            "Printer1",
            Temperature(actual=10, target=60),
            lambda printer: printer.bed,
        )

        await server.loop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server())
