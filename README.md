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

UpdateTime = Annotated[datetime, PastDatetime()]


class Trackable(OpcuaModel):
    ip: IPvAnyAddress = "127.0.0.1"
    last_update: UpdateTime = Field(default_factory=datetime.now)


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

With a server we can create a printer object by calling `server.create`.
The server will return a **proxy** of the object node which can be used for
reading and writing values.

**WARNING**: although the proxy seems to have the same type of the model,
but it is actually an instance of `_OpcuaxPrinter`, which is created
dynamically at runtime.

```python

from examples.tutorial import Printer, Robot
from opcuax import OpcuaServer


async def main(server: OpcuaServer):
    async with server:
        # Create objects under node "0:/Root/0:Objects"
        # Create an object of type Printer named Printer1
        proxy: Printer = await server.create(Printer(), "Printer1")
        await server.create(Printer(), "Printer2")
        await server.create(Robot(), "Robot")

        await server.loop()
```

Now you can verify objects creation by connecting the endpoint in your OPC UA client,
or try [opcua-client-gui](https://github.com/FreeOpcUa/opcua-client-gui) if you don't have one.

![objects-example.png](examples/tutorial_example_objects.png)

Also check 2 created object types under `0:Root/0:Types/0:ObjectTypes/0:BaseObjectType`

![object-types-example.png](examples/tutorial_example_object_types.png)

**Important**: You must call `create_objects` inside an `async with` block, which is required by the
server to prepare itself (init variables, setup endpoint, register namespace, listen to target port...).

### Read All Fields of an Object

We can use the `fetch` function to get a proxy of existing object.

```python
from examples.tutorial import Printer
from opcuax import OpcuaServer, fetch


async def read_object(server: OpcuaServer):
    proxy: Printer = fetch(Printer, "Printer1")
    printer: Printer = await server.read(proxy)

    print(printer.model_dump_json())
```

### Read Single Field of an Object

The proxy remembers our traverse path and performs the same operation
on the object node. `printer1_proxy.latest_job.filename` is equals to
getting the node by path `0:Root/0:Objects/2:Printer1/2:latest_job/2:filename` on the server.

```python
from opcuax import OpcuaServer
from examples.tutorial import Printer, Job


async def read_field(proxy: Printer, server: OpcuaServer):
    job: Job = await server.read(proxy.latest_job)
    filename: str = await server.read(proxy.latest_job.filename)
    assert filename == job.filename
```

### Update All Fields of an Object

```python
from opcuax import OpcuaServer
from examples.tutorial import Printer


async def update_all_nodes(server: OpcuaServer, model: Printer):
    await server.update("Printer1", model)
```

**WARNING**: `proxy = model` is not a valid operation, it makes the variable
"proxy" points to the model.

### Update Single Field of an Object

The proxy remembers all changes and synchronizes all of them after
calling `server.commit`.

Again: `proxy = model` is invalid!

```python
from datetime import datetime

from examples.tutorial import Printer, Job
from opcuax import OpcuaServer


async def update_field(server: OpcuaServer, proxy: Printer):
    proxy.latest_job = Job(filename="A.gcode", time_used=100)
    proxy.last_update = datetime.now()
    proxy.state = "Printing"

    await server.commit(proxy)
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

This part is same as working with a server, except you **cannot** create new object types,
or objects whose types is not included on the server.

```python
import asyncio

from examples.tutorial import Printer, Job
from opcuax import OpcuaClient, fetch


async def main(client: OpcuaClient):
    # wait until server is ready if you run server and client in one program
    await asyncio.sleep(2)

    async with client:
        proxy = fetch(Printer, "Printer1")

        printer: Printer = await client.read(proxy)
        print(printer.model_dump_json())

        proxy.latest_job = Job(filename="A.gcode", time_used=1)
        await client.commit(proxy)
```

[//]: # (## Editor Support)

[//]: # ()

[//]: # (Returned type of `get` function can be inferred with a [pyright]&#40;https://github.com/microsoft/pyright&#41; server.)

[//]: # ()

[//]: # (![editor-support.png]&#40;examples/editor-support.png&#41;)

## Contribute

Please open an issue before coding in case you waste time on unwanted changes,
and follow the [contribution guideline](./CONTRIBUTING.md)

## Resources

* [OPC UA Document](https://reference.opcfoundation.org/)
    * [AddressSpace](https://reference.opcfoundation.org/Core/Part1/v105/docs/6.3.4)
    * [NodeId](https://reference.opcfoundation.org/DI/v104/docs/3.3.2.1)
    * [FolderNode](https://reference.opcfoundation.org/Core/Part3/v104/docs/5.5.3#_Ref131474245)
    * [Nested Objects](https://github.com/FreeOpcUa/opcua-asyncio/issues/185#issuecomment-627752985)
