from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Any, NamedTuple
from uuid import UUID

from asyncua.ua import VariantType
from pydantic import AnyUrl, IPvAnyAddress, Json
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

__date_format = "%Y-%m-%d"
__datetime_format = "%Y-%m-%d %H:%M:%S.%f"


class _UaVariant(NamedTuple):
    variant_type: VariantType
    default: Any


__mapping = {
    str: _UaVariant(VariantType.String, ""),
    int: _UaVariant(VariantType.Int64, 0),
    float: _UaVariant(VariantType.Float, 0),
    bool: _UaVariant(VariantType.Boolean, False),
    # ISO 8601:2004 is required https://reference.opcfoundation.org/Core/Part6/v104/docs/5.4.2.6
    # Currently not working in clients
    # because client returns a string in format "%Y-%m-%dT%H:%M:%SZ"
    date: _UaVariant(VariantType.String, date.min.strftime(__date_format)),
    datetime: _UaVariant(VariantType.String, datetime.min.strftime(__datetime_format)),
    AnyUrl: _UaVariant(VariantType.String, "http://127.0.0.1/"),
    IPv4Address: _UaVariant(VariantType.String, "127.0.0.1"),
    IPv6Address: _UaVariant(VariantType.String, "::1"),
    IPvAnyAddress: _UaVariant(VariantType.String, "127.0.0.1"),
    Path: _UaVariant(VariantType.String, "/dev/null"),
    UUID: _UaVariant(VariantType.String, ""),
    Json: _UaVariant(VariantType.String, "{}"),
}


def ua_variant(field: FieldInfo) -> _UaVariant:
    cls = field.annotation
    if cls is None or cls not in __mapping:
        raise ValueError(f"cannot map {cls} to ua.VariantType")

    variant_type, default = __mapping[cls]

    if field.default != PydanticUndefined:
        default = field.default
    elif field.default_factory is not None:
        default = field.default_factory()

    return _UaVariant(variant_type, default)


def python_value(cls: type[Any], ua_value: Any) -> Any:
    if cls is date:
        return datetime.strptime(ua_value, __date_format)
    elif cls is datetime:
        return datetime.strptime(ua_value, __datetime_format)
    else:
        return cls(ua_value)
