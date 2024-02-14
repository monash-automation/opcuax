from opcuax import OpcuaClientSettings, OpcuaServerSettings

__url = "opc.tcp://localhost:4840"
__ns = "https://github.com/monash-automation/opcuax"

server_settings = OpcuaServerSettings(
    opcua_server_url=__url,
    opcua_server_name="Opcua Lab Server",
    opcua_server_namespace=__ns,
)

client_settings = OpcuaClientSettings(
    opcua_server_url=__url,
    opcua_server_namespace=__ns,
)
