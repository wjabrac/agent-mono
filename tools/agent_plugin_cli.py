import argparse
import json
from pathlib import Path

TEMPLATE = (
    "from core.tools.registry import ToolSpec\n\n"
    "def run(args):\n"
    "    return {{}}\n\n"
    "spec = ToolSpec(name=\"{name}\", input_model=None, run=run)\n"
)


def create_plugin(name: str) -> None:
    root = Path("plugins") / name
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "version": "0.1.0",
        "entry": f"{name}.py",
        "scopes": [],
        "commands": []
    }
    with open(root / "plugin.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(root / f"{name}.py", "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(name=name))
    print(f"created plugin template at {root}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent")
    sub = parser.add_subparsers(dest="cmd")
    plugin = sub.add_parser("plugin")
    plugin_sub = plugin.add_subparsers(dest="plugin_cmd")
    create = plugin_sub.add_parser("create")
    create.add_argument("name")
    args = parser.parse_args()
    if args.cmd == "plugin" and args.plugin_cmd == "create":
        create_plugin(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
