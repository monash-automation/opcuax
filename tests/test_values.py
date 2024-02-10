from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Annotated, TypeVar

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

T = TypeVar("T", bound=OpcuaModel)


async def create_and_read(server: OpcuaServer, model: T) -> T:
    proxy = await server.create("model", model)
    return await server.read(proxy)


async def test_non_negative_float(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: NonNegativeFloat

    node = await server.create_ua_object_type(Model)
    assert node is not None


async def test_default_date(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: date = date(2012, 12, 1)

    model = await create_and_read(server, Model())

    assert model.val == date(2012, 12, 1)


async def test_date_default_factory(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: date = Field(default_factory=date.today)

    model = await create_and_read(server, Model())

    assert model.val == date.today()


async def test_datetime_default_factory(server: OpcuaServer) -> None:
    class Model(OpcuaModel):
        val: datetime = Field(default_factory=datetime.now)

    model = await create_and_read(server, Model())

    assert model.val < datetime.now()


async def test_default_datetime(server: OpcuaServer) -> None:
    t = datetime.now()

    class Model(OpcuaModel):
        val: datetime = t

    model = await create_and_read(server, Model())

    assert model.val == t


async def test_past_date(server: OpcuaServer) -> None:
    t = date(2012, 12, 1)

    class Model(OpcuaModel):
        val: Annotated[date, PastDate()]

    model = await create_and_read(server, Model(val=t))

    assert model.val == t


async def test_past_datetime(server: OpcuaServer) -> None:
    t = datetime.now()

    class Model(OpcuaModel):
        val: Annotated[datetime, PastDatetime(), Field(default_factory=datetime.now)]

    model = await create_and_read(server, Model(val=t))

    assert model.val == t


async def test_future_date(server: OpcuaServer) -> None:
    t = date(2999, 12, 1)

    class Model(OpcuaModel):
        val: Annotated[date, FutureDate()]

    model = await create_and_read(server, Model(val=t))

    assert model.val == t


async def test_any_url(server: OpcuaServer) -> None:
    url = "http://127.0.0.1/"

    class Model(OpcuaModel):
        val: AnyUrl

    model = await create_and_read(server, Model(val=AnyUrl(url)))

    assert str(model.val) == url


async def test_redis_url(server: OpcuaServer) -> None:
    url = "redis://localhost:6379/0"

    class Model(OpcuaModel):
        val: RedisDsn

    model = await create_and_read(server, Model(val=RedisDsn(url)))

    assert str(model.val) == url


async def test_ip_any_address(server: OpcuaServer) -> None:
    addr = "192.168.0.1"

    class Model(OpcuaModel):
        val: IPvAnyAddress

    model = await create_and_read(server, Model(val=addr))

    assert str(model.val) == addr


async def test_ipv4_address(server: OpcuaServer) -> None:
    addr = IPv4Address("192.168.0.1")

    class Model(OpcuaModel):
        val: IPv4Address

    model = await create_and_read(server, Model(val=addr))

    assert model.val == addr


async def test_ipv6_address(server: OpcuaServer) -> None:
    addr = IPv6Address("2001:db8:3333:4444:5555:6666:7777:8888")

    class Model(OpcuaModel):
        val: IPv6Address

    model = await create_and_read(server, Model(val=addr))

    assert model.val == addr


async def test_path(server: OpcuaServer) -> None:
    path = Path("/usr/local/bin")

    class Model(OpcuaModel):
        val: Path

    model = await create_and_read(server, Model(val=path))

    assert model.val == path


async def test_dir_path(server: OpcuaServer) -> None:
    path = Path("./")

    class Model(OpcuaModel):
        val: DirectoryPath

    model = await create_and_read(server, Model(val=path))

    assert model.val == path
