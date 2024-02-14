import asyncio
from collections.abc import Callable
from typing import Any

from asyncua import Client, Node, Server, ua

from benchmark._config import client_settings, server_settings
from benchmark._helper import Timer, random_printer
from benchmark._models import Printer, PrinterHead, PrinterJob, Temperature


async def setup_server() -> tuple[Server, int]:
    server = Server()
    await server.init()

    server.set_endpoint(str(server_settings.opcua_server_url))
    server.set_server_name(str(server_settings.opcua_server_name))
    server.set_security_policy(
        [
            ua.SecurityPolicyType.NoSecurity,
            ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ua.SecurityPolicyType.Basic256Sha256_Sign,
        ]
    )

    ns: int = await server.register_namespace(server_settings.opcua_server_namespace)

    return server, ns


async def create_temperature(ns: int, name: str, parent: Node) -> list[Node]:
    bed = await parent.add_object(ns, name)
    actual = await bed.add_variable(ns, "actual", 0.0)
    target = await bed.add_variable(ns, "target", 0.0)

    return [bed, actual, target]


async def create_head(ns: int, parent: Node) -> list[Node]:
    head = await parent.add_object(ns, "head")
    x = await head.add_variable(ns, "x", 0.0)
    y = await head.add_variable(ns, "y", 0.0)
    z = await head.add_variable(ns, "z", 0.0)

    return [head, x, y, z]


async def create_job(ns: int, parent: Node) -> list[Node]:
    job = await parent.add_object(ns, "job")
    file = await job.add_variable(ns, "file", "N/A")
    progress = await job.add_variable(ns, "progress", 0.0)
    time_left = await job.add_variable(ns, "time_left", 0.0)
    time_left_approx = await job.add_variable(ns, "time_left_approx", 0.0)
    time_used = await job.add_variable(ns, "time_used", 0.0)

    return [job, file, progress, time_left, time_left_approx, time_used]


async def crate_printer_type(server: Server, ns: int) -> Node:
    printer = await server.nodes.base_object_type.add_object_type(ns, "Printer")

    state = await printer.add_variable(ns, "state", "N/A")
    bed_temp = await create_temperature(ns, "bed", printer)
    noz_temp = await create_temperature(ns, "nozzle", printer)
    head = await create_head(ns, printer)
    job = await create_job(ns, printer)

    for node in [state, *bed_temp, *noz_temp, *head, *job]:
        await node.set_modelling_rule(True)

    for node in [state, *bed_temp[1:], *noz_temp[1:], *head[1:], *job[1:]]:
        await node.set_writable(True)

    return printer


async def create_printers(
    server: Server, ns: int, printer_type: Node, n: int = 1
) -> list[Node]:
    printers = []
    for i in range(1, n + 1):
        name = f"Printer{i}"
        printer = await server.nodes.objects.add_object(
            ns, name, objecttype=printer_type.nodeid
        )
        printers.append(printer)
    return printers


def get_browse_name(ns: int) -> Callable[[str], str]:
    return lambda name: f"{ns}:{name}"


async def read_temperature(ns: int, parent: Node) -> Temperature:
    name = get_browse_name(ns)
    actual = await parent.get_child(name("actual"))
    target = await parent.get_child(name("target"))

    await actual.read_value()
    await target.read_value()

    return Temperature(
        actual=await actual.read_value(), target=await target.read_value()
    )


async def read_head(ns: int, parent: Node) -> PrinterHead:
    name = get_browse_name(ns)
    x = await parent.get_child(name("x"))
    y = await parent.get_child(name("y"))
    z = await parent.get_child(name("z"))

    return PrinterHead(
        x=await x.read_value(), y=await y.read_value(), z=await z.read_value()
    )


async def read_job(ns: int, parent: Node) -> PrinterJob:
    name = get_browse_name(ns)
    file = await parent.get_child(name("file"))
    progress = await parent.get_child(name("progress"))
    time_left = await parent.get_child(name("time_left"))
    time_left_approx = await parent.get_child(name("time_left_approx"))
    time_used = await parent.get_child(name("time_used"))

    await progress.read_value()
    await time_left.read_value()
    await time_left_approx.read_value()
    await time_used.read_value()

    return PrinterJob(
        file=await file.read_value(),
        progress=await progress.read_value(),
        time_left=await time_left.read_value(),
        time_left_approx=await time_left_approx.read_value(),
        time_used=await progress.read_value(),
    )


async def read_printer(ns: int, printer: Node) -> Printer:
    name = get_browse_name(ns)
    state: Node = await printer.get_child(name("state"))
    bed: Node = await printer.get_child(name("bed"))
    nozzle: Node = await printer.get_child(name("nozzle"))
    head: Node = await printer.get_child(name("head"))
    job: Node = await printer.get_child(name("job"))

    return Printer(
        state=await state.read_value(),
        bed=await read_temperature(ns, bed),
        nozzle=await read_temperature(ns, nozzle),
        head=await read_head(ns, head),
        job=await read_job(ns, job),
    )


async def write(node: Node, value: Any) -> None:
    var_type = await node.read_data_type_as_variant_type()
    ua_value = ua.DataValue(ua.Variant(value, var_type))
    await node.write_value(ua_value)


async def write_head(ns: int, parent: Node, value: PrinterHead) -> None:
    name = get_browse_name(ns)
    x = await parent.get_child(name("x"))
    y = await parent.get_child(name("y"))
    z = await parent.get_child(name("z"))

    await write(x, value.x)
    await write(y, value.y)
    await write(z, value.z)


async def write_temperature(ns: int, parent: Node, value: Temperature) -> None:
    name = get_browse_name(ns)
    actual = await parent.get_child(name("actual"))
    target = await parent.get_child(name("target"))

    await write(actual, value.actual)
    await write(target, value.target)


async def write_job(ns: int, parent: Node, value: PrinterJob) -> None:
    name = get_browse_name(ns)
    file = await parent.get_child(name("file"))
    progress = await parent.get_child(name("progress"))
    time_left = await parent.get_child(name("time_left"))
    time_left_approx = await parent.get_child(name("time_left_approx"))
    time_used = await parent.get_child(name("time_used"))

    await write(file, value.file)
    await write(progress, value.progress)
    await write(time_left, value.time_left)
    await write(time_left_approx, value.time_left_approx)
    await write(time_used, value.time_used)


async def write_printer(ns: int, printer: Node, value: Printer) -> None:
    name = get_browse_name(ns)
    state: Node = await printer.get_child(name("state"))
    bed: Node = await printer.get_child(name("bed"))
    nozzle: Node = await printer.get_child(name("nozzle"))
    head: Node = await printer.get_child(name("head"))
    job: Node = await printer.get_child(name("job"))

    await write(state, value.state)
    await write_temperature(ns, bed, value.bed)
    await write_temperature(ns, nozzle, value.nozzle)
    await write_head(ns, head, value.head)
    await write_job(ns, job, value.job)


async def server_read_benchmark(printers: int, n: int) -> None:
    server, ns = await setup_server()
    printer_type = await crate_printer_type(server, ns)
    printer_nodes = await create_printers(server, ns, printer_type, n=printers)

    async with server:
        timer = Timer("asyncua", "server-read", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for node in printer_nodes:
                    tg.create_task(read_printer(ns, node))

        timer.end()


async def server_write_benchmark(printers: int, n: int) -> None:
    server, ns = await setup_server()
    printer_type = await crate_printer_type(server, ns)
    printer_nodes = await create_printers(server, ns, printer_type, n=printers)

    async with server:
        timer = Timer("asyncua", "server-write", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for node in printer_nodes:
                    tg.create_task(write_printer(ns, node, random_printer()))

        timer.end()


async def client_read_benchmark(printers: int, n: int) -> None:
    server, ns = await setup_server()
    printer_type = await crate_printer_type(server, ns)
    await create_printers(server, ns, printer_type, n=printers)

    async with server, Client(url=str(client_settings.opcua_server_url)) as client:
        printer_nodes = [
            await client.get_objects_node().get_child(f"{ns}:Printer{i+1}")
            for i in range(printers)
        ]

        timer = Timer("asyncua", "client-read", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for node in printer_nodes:
                    tg.create_task(read_printer(ns, node))

        timer.end()


async def client_write_benchmark(printers: int, n: int) -> None:
    server, ns = await setup_server()
    printer_type = await crate_printer_type(server, ns)
    await create_printers(server, ns, printer_type, n=printers)

    async with server, Client(url=str(client_settings.opcua_server_url)) as client:
        printer_nodes = [
            await client.get_objects_node().get_child(f"{ns}:Printer{i+1}")
            for i in range(printers)
        ]

        timer = Timer("asyncua", "client-write", printers, n)
        timer.start()

        for _ in range(n):
            async with asyncio.TaskGroup() as tg:
                for node in printer_nodes:
                    tg.create_task(write_printer(ns, node, random_printer()))

        timer.end()
