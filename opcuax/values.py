from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Any, NamedTuple
from uuid import UUID

from asyncua.ua import VariantType
from pydantic import (
    AnyUrl,
    FutureDate,
    FutureDatetime,
    IPvAnyAddress,
    Json,
    PastDate,
    PastDatetime,
    UrlConstraints,
)
from pydantic.fields import FieldInfo
from pydantic.types import PathType
from pydantic_core import PydanticUndefined


class _UaVariant(NamedTuple):
    variant_type: VariantType
    default: Any


__mapping = {
    str: _UaVariant(VariantType.String, ""),
    int: _UaVariant(VariantType.Int64, 0),
    float: _UaVariant(VariantType.Float, 0),
    bool: _UaVariant(VariantType.Boolean, False),
    # ISO 8601:2004 is required https://reference.opcfoundation.org/Core/Part6/v104/docs/5.4.2.6
    date: _UaVariant(VariantType.DateTime, date.min),
    FutureDate: _UaVariant(VariantType.DateTime, date.max),
    PastDate: _UaVariant(VariantType.DateTime, date.min),
    datetime: _UaVariant(VariantType.DateTime, datetime.min),
    FutureDatetime: _UaVariant(VariantType.DateTime, datetime.max),
    PastDatetime: _UaVariant(VariantType.DateTime, datetime.max),
    AnyUrl: _UaVariant(VariantType.String, "http://127.0.0.1/"),
    IPv4Address: _UaVariant(VariantType.String, "127.0.0.1"),
    IPv6Address: _UaVariant(VariantType.String, "::1"),
    IPvAnyAddress: _UaVariant(VariantType.String, "127.0.0.1"),
    Path: _UaVariant(VariantType.String, "/dev/null"),
    UUID: _UaVariant(VariantType.String, ""),
    Json: _UaVariant(VariantType.String, "{}"),
}


def default_url(constraint: UrlConstraints) -> str:
    url = ""

    if constraint.allowed_schemes and len(constraint.allowed_schemes) > 0:
        url += constraint.allowed_schemes[0] + "://"

    if constraint.default_host is not None:
        url += constraint.default_host

    if constraint.default_port is not None:
        url += f":{constraint.default_port}"

    if constraint.default_path is not None:
        url += constraint.default_path

    return url


def ua_variant(field: FieldInfo) -> _UaVariant:
    cls = field.annotation
    if cls is None or cls not in __mapping:
        raise ValueError(f"cannot map {cls} to ua.VariantType")

    variant_type, default = __mapping[cls]

    if len(field.metadata) > 0:
        metadata = field.metadata[0]

        # if cls is float or cls is int:
        #     pass
        if isinstance(metadata, UrlConstraints):
            default = default_url(metadata)
        elif isinstance(metadata, (FutureDate, PastDate, FutureDatetime, PastDatetime)):
            variant_type, default = __mapping[type(metadata)]
        elif isinstance(metadata, PathType):
            if metadata.path_type == "dir":
                default = "./"

    if field.default != PydanticUndefined:
        default = field.default
    elif field.default_factory is not None:
        default = field.default_factory()

    return _UaVariant(variant_type, default)


def opcua_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool, date, datetime)):
        return value
    return str(value)


def python_value(cls: type[Any], ua_value: Any) -> Any:
    if cls is date or cls is datetime:
        return ua_value
    else:
        return cls(ua_value)
