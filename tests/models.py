from pydantic import BaseModel

from opcuax.models import OpcuaObjects


class PetOwner(BaseModel):
    name: str
    address: str


class Pet(BaseModel):
    name: str
    age: int
    weight: float

    owner: PetOwner


class Dog(Pet):
    food: str


class Puppy(Dog):
    birthday: str


class Home(BaseModel):
    dog1: Puppy
    dog2: Puppy


class Pets(OpcuaObjects):
    kitty: Pet
    puppy: Puppy
