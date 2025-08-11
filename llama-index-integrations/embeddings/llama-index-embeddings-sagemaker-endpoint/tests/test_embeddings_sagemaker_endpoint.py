from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.embeddings.sagemaker_endpoint import SageMakerEmbedding


def test_text_inference_embedding_class():
    names_of_base_classes = [b.__name__ for b in SageMakerEmbedding.__mro__]
    assert BaseEmbedding.__name__ in names_of_base_classes
