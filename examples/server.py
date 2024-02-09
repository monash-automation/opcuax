import asyncio
import logging

from opcuax import OpcuaObject, OpcuaServer, OpcuaServerSettings

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
        printer1_object: OpcuaObject[Printer] = await server.create(
            Printer(), "Printer1"
        )
        await server.create(Printer(), "Printer2")
        await server.create(Printer(), "Printer3")

        # Read an object
        printer1: Printer = await printer1_object.get()
        print(f"Printer1: {printer1.model_dump()}")

        # Read a certain field
        job_file: str = await printer1_object.get(lambda printer: printer.job.file)
        bed_temp: Temperature = await printer1_object.get(lambda printer: printer.bed)
        print(f"job file: {job_file}, bed temperature: {bed_temp.model_dump()}")

        # Update all fields
        printer1.state = "Printing"
        printer1.nozzle = Temperature(actual=20, target=100)
        await printer1_object.set(printer1)

        # Update a certain field
        await printer1_object.set("Ready", lambda printer: printer.state)
        await printer1_object.set(
            Temperature(actual=10, target=60),
            lambda printer: printer.bed,
        )

        await server.loop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server())
