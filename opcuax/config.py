from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class Template(BaseModel):
    instance_numbers: dict[str, int]
    base_fields: dict[str, Any]
    types: dict[str, Any]


class Keys(StrEnum):
    instances = "instances"
    numbers = "numbers"
    base = "Base"


def parse_config(config: dict[str, Any]):
    instance_numbers = parse_instance_numbers(config)
    base_fields = config.get(Keys.base, {})
    types = {k: v for k, v in config.items() if k not in set(Keys)}

    return Template(
        instance_numbers=instance_numbers, types=types, base_fields=base_fields
    )


def parse_instance_numbers(config: dict[str, Any]) -> dict[str, int]:
    return config.get(Keys.instances, {}).get(Keys.numbers, {})
