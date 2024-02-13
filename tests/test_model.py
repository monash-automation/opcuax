from opcuax.model import EnhancedModel, enhanced_model_class

from tests.models import Dog


async def test_enhancement():
    cls = enhanced_model_class(Dog)
    dog = cls(name="dog", age=11, weight=23)
    assert isinstance(dog, Dog)
    assert isinstance(dog, EnhancedModel)
