from opcuax import OpcuaModel


class Dog(OpcuaModel):
    name: str
    age: int
    weight: float


class Home(OpcuaModel):
    name: str
    address: str

    dog: Dog
