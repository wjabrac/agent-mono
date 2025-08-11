from llama_index.readers.dashscope import DashScopeParse
from llama_index.core.readers.base import BasePydanticReader


def test_class():
    names_of_base_classes = [b.__name__ for b in DashScopeParse.__mro__]
    assert BasePydanticReader.__name__ in names_of_base_classes
