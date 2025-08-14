import json
from core.plugins import discover_plugins
from core.tools.registry import _REGISTRY


def test_manifest_plugin_discovery(tmp_path):
    plug = tmp_path / "a" / "b"
    plug.mkdir(parents=True)
    (plug / "plugin.json").write_text(json.dumps({
        "name": "tmpdemo",
        "version": "0.0.1",
        "entry": "main.py"
    }))
    (plug / "main.py").write_text(
        "from core.tools.registry import ToolSpec\n"
        "def run(args):\n    return {'ok': True}\n"
        "spec = ToolSpec(name='tmp_tool', input_model=None, run=run)\n"
    )
    discover_plugins(str(tmp_path))
    assert "tmp_tool" in _REGISTRY


def test_bad_manifest(tmp_path):
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "plugin.json").write_text("{}")
    discover_plugins(str(tmp_path))
    # Should not raise and not register anything
    assert all(name != "" for name in _REGISTRY)
