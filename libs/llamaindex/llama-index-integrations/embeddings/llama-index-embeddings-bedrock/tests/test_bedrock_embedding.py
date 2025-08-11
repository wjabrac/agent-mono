from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.bedrock import BedrockEmbedding


def test_class():
    names_of_base_classes = [b.__name__ for b in BedrockEmbedding.__mro__]
    assert BaseEmbedding.__name__ in names_of_base_classes
