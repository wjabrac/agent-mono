import sys
from pathlib import Path

from core.plugins.loader import load_plugin
from core.tools.registry import get, _REGISTRY


def _write_plugin(path: Path, name: str) -> None:
    code = (
        "from core.tools.registry import ToolSpec\n"
        "def run(args):\n    return {'name': '%s'}\n"
        "spec = ToolSpec(name='%s', input_model=None, run=run)\n" % (name, name)
    )
    path.write_text(code, encoding="utf-8")


def test_distinct_entry_files(tmp_path):
    _REGISTRY.clear()
    p1 = tmp_path / "p1"
    p2 = tmp_path / "p2"
    p1.mkdir(); p2.mkdir()
    entry1 = p1 / "entry.py"
    entry2 = p2 / "entry.py"
    _write_plugin(entry1, "alpha")
    _write_plugin(entry2, "beta")

    load_plugin(str(entry1))
    load_plugin(str(entry2))

    assert get("alpha").name == "alpha"
    assert get("beta").name == "beta"

    mods = [m for m in sys.modules if m.startswith("_plugin_entry")]
    assert len(mods) == 2
