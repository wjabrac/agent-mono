import json
import logging
import importlib
from pydantic import BaseModel
import pytest


def test_load_manifest_logs_validation_error(tmp_path, monkeypatch, caplog):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("TOOLS_MANIFEST_PATH", str(manifest_path))
    from core.tools import manifest as mf
    importlib.reload(mf)

    class Dummy(BaseModel):
        x: int

    def fake_load(_):
        Dummy.model_validate({"x": "bad"})

    monkeypatch.setattr(mf.json, "load", fake_load)
    with caplog.at_level(logging.ERROR):
        assert mf.load_manifest() == {}
    assert "failed to load manifest" in caplog.text.lower()


def test_load_manifest_unexpected_exception(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("TOOLS_MANIFEST_PATH", str(manifest_path))
    from core.tools import manifest as mf
    importlib.reload(mf)

    def boom(_):
        raise RuntimeError("boom")

    monkeypatch.setattr(mf.json, "load", boom)
    with pytest.raises(RuntimeError):
        mf.load_manifest()
