import argparse
import json
from pathlib import Path

TEMPLATE = (
    "from core.tools.registry import ToolSpec\n\n"
    "def run(args):\n"
    "    return {{}}\n\n"
    "spec = ToolSpec(name=\"{name}\", input_model=None, run=run)\n"
)


def create_plugin(name: str, root: Path) -> None:
    """Scaffold a basic Python plugin."""
    plugin_dir = root / "plugins" / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "version": "0.1.0",
        "entry": f"{name}.py",
        "scopes": [],
        "commands": [],
    }
    with open(plugin_dir / "plugin.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    with open(plugin_dir / f"{name}.py", "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(name=name))
    print(f"created plugin template at {plugin_dir}")


SERVICE_TEMPLATE = """from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
"""


def create_service(name: str, root: Path) -> None:
    """Scaffold a minimal FastAPI service."""
    service_dir = root / "services" / name
    service_dir.mkdir(parents=True, exist_ok=True)
    with open(service_dir / "main.py", "w", encoding="utf-8") as f:
        f.write(SERVICE_TEMPLATE)
    print(f"created service template at {service_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent")
    sub = parser.add_subparsers(dest="cmd")

    create = sub.add_parser("create")
    create.add_argument("type", choices=["plugin", "service"])
    create.add_argument("name")
    create.add_argument("--root", default=".")

    args = parser.parse_args()
    if args.cmd == "create":
        root = Path(args.root)
        if args.type == "plugin":
            create_plugin(args.name, root)
        elif args.type == "service":
            create_service(args.name, root)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
