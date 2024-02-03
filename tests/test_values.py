from pydantic import BaseModel, NonNegativeFloat

from opcuax import OpcuaObjects, OpcuaServer


class NonNegFloat(BaseModel):
    val: NonNegativeFloat = 0


async def test_non_negative_float(server: OpcuaServer):
    class Objects(OpcuaObjects):
        num: NonNegFloat

    await server.create_objects(Objects)
    objs = await server.read_objects(Objects)
    assert objs.num.val == 0

    objs.num.val = 123.45
    await server.update_objects(objs)
