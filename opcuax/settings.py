from typing import Annotated

from pydantic import AnyUrl, HttpUrl, PositiveFloat, UrlConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

OpcuaUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["opc.tcp"])]


class Settings(BaseSettings):
    opcua_server_url: OpcuaUrl = "opc.tcp://localhost:4840"
    opcua_server_namespace: HttpUrl = "https://github.com/monash-automation/opcuax"


class OpcuaServerSettings(Settings):
    opcua_server_name: str = "OPC UA Server"
    opcua_server_interval: PositiveFloat = 0.1


class OpcuaClientSettings(Settings):
    pass


class EnvOpcuaServerSettings(OpcuaServerSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class EnvOpcuaClientSettings(OpcuaClientSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def display():
    settings = EnvOpcuaServerSettings()
    print(settings.model_dump_json(indent=2))
