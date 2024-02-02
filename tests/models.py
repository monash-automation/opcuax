from opcuax.obj import OpcuaObject
from opcuax.var import OpcuaFloatVar, OpcuaIntVar, OpcuaStrVar


class PetOwner(OpcuaObject):
    name = OpcuaStrVar(name="Name", default="???")
    address = OpcuaStrVar(name="Address", default="TBD")


class Pet(OpcuaObject):
    name = OpcuaStrVar(name="Name", default="unknown")
    age = OpcuaIntVar(name="Age")
    weight = OpcuaFloatVar(name="Weight")

    owner = PetOwner(name="Owner")


class Dog(Pet):
    food = OpcuaStrVar("Food")


class Puppy(Dog):
    birthday = OpcuaStrVar("BirthDay", default="today?")


class Home(OpcuaObject):
    dog1 = Puppy(name="Dog1")
    dog2 = Puppy(name="Dog2")
