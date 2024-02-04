from datetime import date, datetime
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


def opcua_default_value(field: FieldInfo) -> Any:
    if field.default != PydanticUndefined:
        return opcua_value_of(field.default, field)
    elif field.default_factory is not None:
        return opcua_value_of(field.default_factory(), field)

    cls = field.annotation
    if cls is str:
        return ""
    elif cls is int:
        return 0
    elif cls is float:
        return 0.0
    elif cls is bool:
        return False
    elif cls is date:
        return date.min
    elif cls is datetime:
        return datetime.min
    else:
        raise ValueError(f"default value is required for type {field.annotation}")


def opcua_value_of(value: Any, field: FieldInfo) -> Any:
    cls = field.annotation
    assert cls is not None

    if issubclass(cls, (str, int, float, bool)):
        return value
    else:
        return str(value)
