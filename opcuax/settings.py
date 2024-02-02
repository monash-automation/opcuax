from pathlib import Path
from typing import Annotated

from pydantic import AnyUrl, FilePath, HttpUrl, PositiveFloat, RedisDsn, UrlConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

OpcuaUrl = Annotated[AnyUrl, UrlConstraints(allowed_schemes=["opc.tcp"])]


class Settings(BaseSettings):
    opcua_server_url: OpcuaUrl = "opc.tcp://localhost:4840"
    interval: PositiveFloat = 0.1


class ServerSettings(Settings):
    metadata_file: FilePath = Path("objects.toml")
    opcua_server_name: str = "Monash Automation OPC UA Server"
    opcua_server_namespace: HttpUrl = "http://monashautomation.com/server/opcua"


class ClientSettings(Settings):
    opcua_server_namespace: HttpUrl = "http://monashautomation.com/server/opcua"


class WorkerSettings(Settings):
    redis_url: RedisDsn = "redis://127.0.0.1:6379"


class EnvServerSettings(ServerSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class EnvClientSettings(ClientSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


def display():
    settings = EnvServerSettings()
    print(settings.model_dump_json(indent=2))
