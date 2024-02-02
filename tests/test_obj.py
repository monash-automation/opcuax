import pytest_asyncio

from .models import Pet, PetOwner, Puppy


@pytest_asyncio.fixture
async def kitty(pet_server) -> Pet:
    yield await pet_server.get_object(Pet, "Kitty")


@pytest_asyncio.fixture
async def puppy(pet_server) -> Puppy:
    yield await pet_server.get_object(Puppy, "Puppy")


async def test_get_object(pet_server):
    pet = await pet_server.get_object(Pet, "Kitty")

    assert isinstance(pet, Pet)


async def test_get_default_value(kitty):
    name = await kitty.name.get()
    assert name == Pet.name.default


async def test_get_from_nested_object(kitty):
    owner_name = await kitty.owner.name.get()
    assert owner_name == PetOwner.name.default


async def test_set(kitty):
    await kitty.name.set("foo")

    name = await kitty.name.get()
    assert name == "foo"


async def test_set_nested_object_field(kitty):
    await kitty.owner.name.set("foo")

    owner_name = await kitty.owner.name.get()
    assert owner_name == "foo"


async def test_inheritance(puppy):
    name = await puppy.name.get()
    assert name == Pet.name.default

    food = await puppy.food.get()
    assert food == Puppy.food.default


async def test_to_dict(kitty):
    data = await kitty.to_dict()

    assert data == {
        Pet.name.ua_name: Pet.name.default,
        Pet.age.ua_name: Pet.age.default,
        Pet.weight.ua_name: Pet.weight.default,
        Pet.owner.ua_name: {
            PetOwner.name.ua_name: PetOwner.name.default,
            PetOwner.address.ua_name: PetOwner.address.default,
        },
    }


async def test_inheritance_to_dict(puppy):
    data = await puppy.to_dict()

    assert data == {
        Puppy.name.ua_name: Puppy.name.default,
        Puppy.age.ua_name: Puppy.age.default,
        Puppy.weight.ua_name: Puppy.weight.default,
        Puppy.owner.ua_name: {
            PetOwner.name.ua_name: PetOwner.name.default,
            PetOwner.address.ua_name: PetOwner.address.default,
        },
        Puppy.food.ua_name: Puppy.food.default,
        Puppy.birthday.ua_name: Puppy.birthday.default,
    }


async def test_to_flattened_dict(kitty):
    data = await kitty.to_dict(flatten=True)

    assert data == {
        Pet.name.ua_name: Pet.name.default,
        Pet.age.ua_name: Pet.age.default,
        Pet.weight.ua_name: Pet.weight.default,
        "Owner.Name": PetOwner.name.default,
        "Owner.Address": PetOwner.address.default,
    }
