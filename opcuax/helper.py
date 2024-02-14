from typing import Any

from pydantic.fields import FieldInfo


def field_class(info: FieldInfo) -> type[Any]:
    cls = info.annotation
    assert cls is not None
    return cls
