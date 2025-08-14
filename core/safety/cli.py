from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.loader import PluginLoader
from .permissions import PermissionChecker
from .executor import Executor


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    run_p = sub.add_parser("run")
    run_p.add_argument("plugin")
    run_p.add_argument("command")
    run_p.add_argument("--json-args", default="{}")
    args = parser.parse_args()
    if args.cmd != "run":
        parser.error("unknown command")
    loader = PluginLoader()
    plugin_dir = Path("core/plugins") / args.plugin
    plugin = loader.load(plugin_dir)
    checker = PermissionChecker()
    checker.register_plugin(plugin.manifest.name, set(plugin.manifest.scopes_allow), plugin.manifest.rate_limit_per_min)
    executor = Executor(checker)
    result = executor.execute(
        plugin, args.command, json.loads(args.json_args), actor="cli"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
