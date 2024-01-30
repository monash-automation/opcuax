# OPC UA Server

## Build

[Install poetry](https://python-poetry.org/docs/) and install dependencies

```shell
poetry install
```

## Run

```shell
poetry run start
```

Connect to `opc.tcp://localhost:4840` with your OPC UA client.

![example.png](example.png)

## Objects

The [objects.toml](./objects.toml) contains metadata for object nodes.
I chose [TOML](https://toml.io/en/) because it is more human friendly than YAML and JSON.

`Base` (base class) contains fields for all server objects.

```toml
[Base]
heartbeat = 0
status = "offline"
```

This is equivalent to the Python code below:

```python
class Base:
    heartbeat = 0
    status = "offline"


class Printer(Base):
    pass
```

`Printer.Control` contains fields for a nested object named `Control`.
If you do not have nested object fields, just use `Printer`.

```toml
[Printer]
State = "Error"

[Printer.Control]
PartRemoved = false
BedCleaned = false
File = "Unknown"
```

This is equivalent to the Python code below:

```python
class PrinterControl:
    PartRemoved = False
    BedCleaned = False
    File = "Unknown"


class Printer:
    State = "Error"
    Control = PrinterControl()
```

`instance.numbers` contains number of instances you want to create for each object type.

```toml
[instances.numbers]
Printer = 3
```

## Pitfalls

Please use `0.0` for float numbers, `0` will be parsed as int.

Namespace indices of object nodes starts from `10`.

## Client

Given the object type below:

```toml
[Printer.LatestJob]
Progress = 0.0
```

### asyncua.Client

To get value of field `Progress`, we can use a client to
get the target node by browse names (`bname`)

```python
from asyncua import Client, ua


async def main():
    async with Client(url="opc.tcp://localhost:4840") as client:
        root = client.get_objects_node()

        # traverse from root
        printer = await root.get_child("Printer1")
        job = await printer.get_child("LatestJob")
        progress = await job.get_child("Progress")

        # traverse by path
        assert progress == await root.get_child("Printer1/LatestJob/Progress")

        # read value
        cur_progress = await progress.get_value()
        print(cur_progress)

        # write value
        data_type = await progress.read_data_type_as_variant_type()
        assert data_type == ua.VariantType.Double
        await progress.write_value(ua.DataValue(ua.Variant(99, data_type)))
```

## opcuax.client

If you want to access nodes in the OOP way, you can try `OpcuaClient`:

```python
from opcuax.client import OpcuaClient, OpcuaObject, OpcuaFloatVar, OpcuaStrVar


class PrinterJob(OpcuaObject):
  progress = OpcuaFloatVar(name="Progress")


class Printer(OpcuaObject):
  state = OpcuaStrVar(name="State")
  job = PrinterJob(name="LatestJob")


async def main():
  async with OpcuaClient(url="opc.tcp://localhost:4840") as client:
    printer = await client.get_object(Printer, name="Printer1")

    # get value
    cur_state = await printer.state.get()
    print(cur_state)

    # set value
    await printer.job.progress.set(99)
```

## Contribute

Fork the project and clone.

Config Git with your username and email.

```shell
git config --global user.name 'your name'
git config --global user.email 'your email'
```

Install pre-commit hooks

```shell
pip install pre-commit
pre-commit install
```

Code and commit.

Push the branch and submit a pull request.

## Grafana Monitor Dashboard

```shell
docker run -d --name=mes-grafana -p 3080:3000 -v grafana:/var/lib/grafana -e "GF_INSTALL_PLUGINS=grafana-clock-panel, grafana-simple-json-datasource, redis-datasource" grafana/grafana-oss
```

## Resources

* [OPC UA Document](https://reference.opcfoundation.org/)
    * [AddressSpace](https://reference.opcfoundation.org/Core/Part1/v105/docs/6.3.4)
    * [NodeId](https://reference.opcfoundation.org/DI/v104/docs/3.3.2.1)
    * [FolderNode](https://reference.opcfoundation.org/Core/Part3/v104/docs/5.5.3#_Ref131474245)
    * [Nested Objects](https://github.com/FreeOpcUa/opcua-asyncio/issues/185#issuecomment-627752985)
* [Book from qiyuqi](https://qiyuqi.gitbooks.io/opc-ua/content/Part3/Chapter4.html)

## Future

* Backup and restore data after server restarted
* Move endpoint and server name to `.env` file
* Use Pydantic classes
  as [object node declaration](https://github.com/monash-automation/mes-printing-server/blob/main/src/opcuax/objects.py)
* [Record history Data](https://github.com/FreeOpcUa/opcua-asyncio/blob/master/examples/server-datavalue-history.py)
