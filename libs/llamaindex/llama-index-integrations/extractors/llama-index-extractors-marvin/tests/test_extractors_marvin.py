import sys
import types
import pathlib

import asyncio
import importlib.util
import pytest
from pydantic import BaseModel

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

marvin_base_path = pathlib.Path(__file__).resolve().parents[1] / "llama_index" / "extractors" / "marvin" / "base.py"
spec = importlib.util.spec_from_file_location("marvin_base", marvin_base_path)
marvin_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(marvin_base)  # type: ignore
MarvinMetadataExtractor = marvin_base.MarvinMetadataExtractor

core_schema_path = pathlib.Path(__file__).resolve().parents[3] / "llama-index-core" / "llama_index" / "core" / "schema.py"
spec2 = importlib.util.spec_from_file_location("schema", core_schema_path)
schema = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(schema)  # type: ignore
TextNode = schema.TextNode


class DummyModel(BaseModel):
    foo: str


def test_marvin_extractor_mock(monkeypatch):
    async def fake_cast_async(text, target):
        return DummyModel(foo="bar")

    fake_module = types.SimpleNamespace(cast_async=fake_cast_async)
    monkeypatch.setitem(sys.modules, "marvin", fake_module)

    extractor = MarvinMetadataExtractor(marvin_model=DummyModel)
    res = asyncio.run(extractor.aextract([TextNode(text="hello")]))
    assert res == [{"marvin_metadata": {"foo": "bar"}}]
