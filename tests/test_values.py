from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Annotated

from opcuax import OpcuaModel, OpcuaServer
from pydantic import (
    AnyUrl,
    DirectoryPath,
    Field,
    FutureDate,
    IPvAnyAddress,
    NonNegativeFloat,
    PastDate,
    PastDatetime,
    RedisDsn,
)


async def test_non_negative_float(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: NonNegativeFloat

    node = await server.create_ua_object_type(Model)
    assert node is not None


async def test_default_date(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: date = date(2012, 12, 1)

    await server.create(Model(), "model")
    model = await server.get(Model, "model")

    assert model.val == date(2012, 12, 1)


async def test_date_default_factory(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: date = Field(default_factory=date.today)

    await server.create(Model(), "model")
    model = await server.get(Model, "model")

    assert model.val == date.today()


async def test_datetime_default_factory(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: datetime = Field(default_factory=datetime.now)

    await server.create(Model(), "model")
    model = await server.get(Model, "model")

    assert model.val < datetime.now()


async def test_default_datetime(server: OpcuaServer) -> None:
    t = datetime.now()

    class Model(OpcuaModel):
        val: datetime = t

    await server.create(Model(), "model")
    model = await server.get(Model, "model")

    assert model.val == t


async def test_past_date(server: OpcuaServer) -> None:
    t = date(2012, 12, 1)

    class Model(OpcuaModel):
        val: Annotated[date, PastDate()]

    await server.create(Model(val=t), "model")
    model = await server.get(Model, "model")

    assert model.val == t


async def test_past_datetime(server: OpcuaServer) -> None:
    t = datetime.now()

    class Model(OpcuaModel):
        val: Annotated[datetime, PastDatetime(), Field(default_factory=datetime.now)]

    await server.create(Model(val=t), "model")
    model = await server.get(Model, "model")

    assert model.val == t


async def test_future_date(server: OpcuaServer) -> None:
    t = date(2032, 12, 1)

    class Model(OpcuaModel):
        val: Annotated[date, FutureDate()]

    await server.create(Model(val=t), "model")
    model = await server.get(Model, "model")

    assert model.val == t


async def test_any_url(server: OpcuaServer) -> None:
    url = "http://127.0.0.1/"

    class Model(OpcuaModel):
        val: AnyUrl

    await server.create(Model(val=AnyUrl(url)), "model")
    model = await server.get(Model, "model")

    assert str(model.val) == url


async def test_redis_url(server: OpcuaServer) -> None:
    url = "redis://localhost:6379/0"

    class Model(OpcuaModel):
        val: RedisDsn

    await server.create(Model(val=RedisDsn(url)), "model")
    model = await server.get(Model, "model")

    assert str(model.val) == url


async def test_ip_any_address(server: OpcuaServer) -> None:
    addr = "192.168.0.1"

    class Model(OpcuaModel):
        val: IPvAnyAddress

    await server.create(Model(val=addr), "model")
    model = await server.get(Model, "model")

    assert str(model.val) == addr


async def test_ipv4_address(server: OpcuaServer) -> None:
    addr = IPv4Address("192.168.0.1")

    class Model(OpcuaModel):
        val: IPv4Address

    await server.create(Model(val=addr), "model")
    model = await server.get(Model, "model")

    assert model.val == addr


async def test_ipv6_address(server: OpcuaServer) -> None:
    addr = IPv6Address("2001:db8:3333:4444:5555:6666:7777:8888")

    class Model(OpcuaModel):
        val: IPv6Address

    await server.create(Model(val=addr), "model")
    model = await server.get(Model, "model")

    assert model.val == addr


async def test_path(server: OpcuaServer) -> None:
    path = Path("/usr/local/bin")

    class Model(OpcuaModel):
        val: Path

    await server.create(Model(val=path), "model")
    model = await server.get(Model, "model")

    assert model.val == path


async def test_dir_path(server: OpcuaServer) -> None:
    path = Path("./")

    class Model(OpcuaModel):
        val: DirectoryPath

    await server.create(Model(val=path), "model")
    model = await server.get(Model, "model")

    assert model.val == path
