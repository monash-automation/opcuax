import copy

import pytest
from opcuax.core import OpcuaxNode, __node_class_prefix, create_node_class

from .models import Dog


@pytest.fixture
def node_class() -> type[OpcuaxNode[Dog]]:
    return create_node_class(Dog)


def test_create_node_class(node_class):
    cls = create_node_class(Dog)
    assert cls.__name__ == __node_class_prefix + Dog.__name__
    assert issubclass(cls, OpcuaxNode)

    for name in Dog.model_fields:
        assert name in cls.__dict__
        assert isinstance(cls.__dict__[name], OpcuaxNode)


def test_node_init(node_class):
    node = node_class(cls=Dog, browse_path=["Snoopy"])
    assert node.updates is None


def test_copy_node(node_class):
    node = node_class(cls=Dog, browse_path=["Snoopy"])
    new_node = copy.copy(node)

    for name in OpcuaxNode.__slots__:
        assert getattr(node, name) == getattr(new_node, name)
