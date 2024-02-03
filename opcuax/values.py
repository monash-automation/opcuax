from datetime import date, datetime
from typing import Any

from pydantic.fields import FieldInfo, PydanticUndefined


def default_value(field: FieldInfo) -> Any:
    if field.default != PydanticUndefined:
        return field.default
    elif field.default_factory is not None:
        return field.default_factory()

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
