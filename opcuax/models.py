import asyncio

import redis.asyncio as redis

from opcuax.client import OpcuaClient, OpcuaObject, OpcuaVariable


class PrinterHead(OpcuaObject):
    x = OpcuaVariable[float](name="X")
    y = OpcuaVariable[float](name="Y")
    z = OpcuaVariable[float](name="Z")


class PrinterJob(OpcuaObject):
    file = OpcuaVariable[str](name="File")
    progress = OpcuaVariable[float](name="Progress")
    time_left = OpcuaVariable[float](name="TimeLeft")
    time_left_approx = OpcuaVariable[float](name="TimeLeftApprox")
    time_used = OpcuaVariable[float](name="TimeUsed")


class Printer(OpcuaObject):
    state = OpcuaVariable[str](name="State")
    noz_act_temp = OpcuaVariable[float](name="NozzleActualTemperature")
    bed_act_temp = OpcuaVariable[float](name="BedActualTemperature")
    noz_tar_temp = OpcuaVariable[float](name="NozzleTargetTemperature")
    bed_tar_temp = OpcuaVariable[float](name="BedTargetTemperature")

    head = PrinterHead(name="Head")
    job = PrinterJob(name="LatestJob")


async def main():
    opcua_client = OpcuaClient(url="opc.tcp://localhost:4840")

    async with opcua_client, redis.Redis() as redis_client:
        printer = await opcua_client.get_object(Printer, name="Printer1")
        data = await printer.to_dict()
        print(data)
        await redis_client.hset("printer1", mapping=data)


if __name__ == "__main__":
    asyncio.run(main())
