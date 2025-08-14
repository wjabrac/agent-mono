import json, textwrap
from pathlib import Path
from core.tools.plugin_manifest import discover_plugins, _loaded
from core.tools.registry import _REGISTRY

def _write_plugin(path: Path):
    path.write_text(textwrap.dedent(
        """
        from core.tools.registry import ToolSpec
        from core.instrumentation import instrument_tool

        @instrument_tool('temp_plugin')
        def run(args):
            return {'ok': True}

        spec = ToolSpec(name='temp_plugin', input_model=None, run=run)
        """
    ))


def test_plugin_manifest_add_and_remove(tmp_path):
    plugin_file = tmp_path / 'plug.py'
    _write_plugin(plugin_file)
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'plugins': [{'path': str(plugin_file)}]}))

    discover_plugins(str(tmp_path))
    assert 'temp_plugin' in _REGISTRY
    assert str(manifest) in _loaded

    manifest.unlink()
    discover_plugins(str(tmp_path))
    assert 'temp_plugin' not in _REGISTRY
    assert str(manifest) not in _loaded
