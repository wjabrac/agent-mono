from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib.util
from types import ModuleType
from typing import List

from .schema import Manifest, validate_manifest
from core.safety import events


@dataclass
class Plugin:
    path: Path
    manifest: Manifest
    module: ModuleType


class PluginLoader:
    """Discover and load plugins from paths."""

    def discover(self, paths: List[str]) -> List[Path]:
        out: List[Path] = []
        for p in paths:
            for child in Path(p).iterdir():
                if (child / "plugin.json").exists():
                    out.append(child)
        return out

    def validate_manifest(self, p: Path) -> Manifest:
        return validate_manifest(p / "plugin.json")

    def load(self, p: Path) -> Plugin:
        manifest = self.validate_manifest(p)
        spec = importlib.util.spec_from_file_location(
            manifest.name, p / f"{manifest.name}.py"
        )
        if spec is None or spec.loader is None:
            raise ImportError("Cannot load plugin module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin = Plugin(path=p, manifest=manifest, module=module)
        events.emit("on_plugin_load", plugin)
        return plugin
