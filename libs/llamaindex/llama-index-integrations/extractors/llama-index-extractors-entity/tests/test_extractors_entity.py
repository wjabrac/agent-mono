import asyncio
import pathlib
import importlib.util
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

entity_base_path = pathlib.Path(__file__).resolve().parents[1] / "llama_index" / "extractors" / "entity" / "base.py"
spec = importlib.util.spec_from_file_location("entity_base", entity_base_path)
entity_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entity_base)  # type: ignore
EntityExtractor = entity_base.EntityExtractor

core_schema_path = pathlib.Path(__file__).resolve().parents[3] / "llama-index-core" / "llama_index" / "core" / "schema.py"
spec2 = importlib.util.spec_from_file_location("schema", core_schema_path)
schema = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(schema)  # type: ignore
TextNode = schema.TextNode


class DummyModel:
    def predict(self, words):
        return [{"span": ["hello"], "label": "PER", "score": 0.9}]


def test_entity_extractor_mock(monkeypatch):
    monkeypatch.setattr(
        "llama_index.extractors.entity.base.SpanMarkerModel.from_pretrained",
        lambda model_name: DummyModel(),
    )
    extractor = EntityExtractor(tokenizer=str.split)
    res = asyncio.run(extractor.aextract([TextNode(text="hello")]))
    assert res == [{"persons": ["hello"]}]
