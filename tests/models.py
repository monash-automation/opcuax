from opcuax import OpcuaModel


class PetOwner(OpcuaModel):
    name: str
    address: str


class Dog(OpcuaModel):
    name: str
    age: int
    weight: float
    # birthday: PastDate
