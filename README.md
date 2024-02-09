# opcuax

A simple OPC UA library based on [opcua-asyncio](https://opcua-asyncio.readthedocs.io/en/latest/)
and [Pydantic](https://docs.pydantic.dev/latest/).

## Code Examples

* [Server](./examples/server.py)
* [Client](./examples/client.py)
* [Cache](./examples/redis_cache.py)
* [Full code](./examples/tutorial.py) of [Getting Started](#getting-started) section

## Getting Started

Suppose we want to run an OPC UA server to record latest data of printers and robots in the lab:

* Printers
    * ip address
    * last update time
    * current state
    * latest job (time used in seconds, filename)
* Robot
    * ip address
    * last update time
    * current position (`(x, y)` both in range `[-200, 200]`)
    * uptime (in seconds)

### Create Models

We first convert the requirement to Python classes using Pydantic `BaseModel`.

Note we extend class `OpcuaModel` in `Printer` and `Robot`
(through a base class `Trackable` to reuse common fields).
`opcuax` will treat `OpcuaModel` subclasses as OPC UA object types for object node creation.
`OpcuaModel` itself is a subclass of `BaseModel` with all Pydantic features.

```python
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, NonNegativeInt, Field, IPvAnyAddress, PastDatetime

from opcuax import OpcuaModel

UpdateTime = Annotated[datetime, PastDatetime(), Field(default_factory=datetime.now)]


class Trackable(OpcuaModel):
    ip: IPvAnyAddress = "127.0.0.1"
    last_update: UpdateTime


class Position(BaseModel):
    x: LabPos = 0
    y: LabPos = 0


class Job(BaseModel):
    filename: str = ""
    time_used: NonNegativeInt = 0


class Printer(Trackable):
    state: str = "Unknown"
    latest_job: Job = Job()


class Robot(Trackable):
    position: Position = Position()
    up_time: NonNegativeInt = 0
```

### Setup Server

To create a server, we need to specify an endpoint, name of the server and a namespace uri for our objects.
This can be done by either using a settings object:

```python
from opcuax import OpcuaServer, OpcuaServerSettings

settings = OpcuaServerSettings(
    opcua_server_url="opc.tcp://localhost:4840",
    opcua_server_name="Opcua Lab Server",
    opcua_server_namespace="https://github.com/monash-automation/opcuax",
)
server = OpcuaServer.from_settings(settings)
```

Or using environment variables or a `.env` file:

```.dotenv
OPCUA_SERVER_URL='opc.tcp://localhost:4840'
OPCUA_SERVER_NAME='Opcua Lab Server'
OPCUA_SERVER_NAMESPACE='https://github.com/monash-automation/opcuax'
```

```python
from opcuax import OpcuaServer

server = OpcuaServer.from_env(env_file=".env")
```

With a server we can create printer and robot objects

```python
from opcuax import OpcuaServer


async def main(server: OpcuaServer):
    async with server:
        # Create objects under node "0:/Root/0:Objects"
        # Create an object of type Printer named Printer1
        await server.create(Printer(), "Printer1")
        await server.create(Printer(), "Printer2")
        await server.create(Robot(), "Robot")

        await server.loop()
```

Now you can verify objects creation by connecting the endpoint in your OPC UA client,
or try [opcua-client-gui](https://github.com/FreeOpcUa/opcua-client-gui) if you don't have one.

![objects-example.png](examples/tutorial_example_objects.png)

Also check 2 created object types under `0:Root/0:Types/0:ObjectTypes/0:BaseObjectType`

![object-types-example.png](examples/tutorial_example_object_types.png)

#### Important

You must call `create_objects` inside an `async with` block, which is required by the
server to prepare itself (init variables, setup endpoint, register namespace, listen to target port...).

### Read All Fields of an Object

```python
async def read_object(server: OpcuaServer):
    printer1 = await server.get(Printer, "Printer1")
    print(printer1.model_dump_json())
```

### Read Single Field of an Object

If we want to read a certain node, we can use a lambda expression to specify the target node.
This also works for an object node, which is not allowed in `asyncua`.

```python
async def read_field(server: OpcuaServer):
    filename = await server.get(Printer, "Printer1", lambda printer: printer.latest_job.filename)
    job = await server.get(Printer, "Printer1", lambda printer: printer.latest_job)
    assert filename == job.filename
```

### Update All Fields of an Object

```python
async def update_object(server: OpcuaServer, printer1: Printer):
    await server.set(Printer, "Printer1", printer1)
    await server.set(Printer, "Printer1", "Ready", lambda printer: printer.state)
```

### Update Single Field of an Object

```python
async def update_field(server: OpcuaServer):
    await server.set(Printer, "Printer1", "Ready", lambda printer: printer.state)
```

### Setup Client

Similar to server, we can create a client by either using a settings object:

```python
from opcuax import OpcuaClient, OpcuaClientSettings

settings = OpcuaClientSettings(
    opcua_server_url="opc.tcp://localhost:4840",
    opcua_server_namespace="https://github.com/monash-automation/opcuax",
)
client = OpcuaClient.from_settings(settings)
```

Or by using environment variables or a `.env` file

```dotenv
OPCUA_SERVER_URL='opc.tcp://localhost:4840'
OPCUA_SERVER_NAMESPACE='https://github.com/monash-automation/opcuax'
```

```python
from opcuax import OpcuaClient

client = OpcuaClient.from_env(env_file=".env")
```

### Read and Update Object Values

This part is same as working with a server, except you use `OpcuaClient.get` and `OpcuaClient.set` functions.

```python
from opcuax import OpcuaClient


async def main(client: OpcuaClient):
    # wait until server is ready if you run server and client in one program
    await asyncio.sleep(2)

    async with client:
        printer1 = await client.get(Printer, "Printer1")
    print(printer1.model_dump_json())

    await client.set(
        Printer,
        "Printer1",
        Job(filename="A.gcode", time_used=1),
        lambda printer: printer.latest_job,
    )
```

## Editor Support

Returned type of `get` function can be inferred with a [pyright](https://github.com/microsoft/pyright) server.

![editor-support.png](examples/editor-support.png)

## Contribute

Please open an issue before coding in case you waste time on unwanted changes,
and follow the [contribution guideline](./CONTRIBUTING.md)

## Resources

* [OPC UA Document](https://reference.opcfoundation.org/)
    * [AddressSpace](https://reference.opcfoundation.org/Core/Part1/v105/docs/6.3.4)
    * [NodeId](https://reference.opcfoundation.org/DI/v104/docs/3.3.2.1)
    * [FolderNode](https://reference.opcfoundation.org/Core/Part3/v104/docs/5.5.3#_Ref131474245)
    * [Nested Objects](https://github.com/FreeOpcUa/opcua-asyncio/issues/185#issuecomment-627752985)
