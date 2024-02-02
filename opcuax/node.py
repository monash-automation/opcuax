from asyncua import Node


class OpcuaNode:
    ua_node: Node
    ua_name: str

    def __init__(self, name: str):
        self.ua_name: str = name

    def clone(self) -> "OpcuaNode":
        return type(self)(name=self.ua_name)

    @property
    def node_id(self) -> str:
        return str(self.ua_node.nodeid)
