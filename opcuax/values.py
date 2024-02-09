from datetime import date, datetime
from pathlib import Path
from typing import Any, NamedTuple
from uuid import UUID

from asyncua.ua import VariantType
from pydantic import AnyUrl, Json
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


class _UaVariant(NamedTuple):
    variant_type: VariantType
    default: Any


__mapping = {
    str: _UaVariant(VariantType.String, ""),
    int: _UaVariant(VariantType.Int64, 0),
    float: _UaVariant(VariantType.Float, 0),
    bool: _UaVariant(VariantType.Boolean, False),
    date: _UaVariant(VariantType.DateTime, date.min),
    datetime: _UaVariant(VariantType.DateTime, datetime.min),
    AnyUrl: _UaVariant(VariantType.String, "http://127.0.0.1/"),
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
        return datetime.strptime(ua_value, "%Y-%m-%d")
    elif cls is datetime:
        return datetime.strptime(ua_value, "%Y-%m-%d %H:%M:%S")
    else:
        return cls(ua_value)
