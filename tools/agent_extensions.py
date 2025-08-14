import json
from pathlib import Path
from typing import Iterable


def flow_validate(path: str) -> int:
    """Validate a flow JSON file with basic checks."""
    p = Path(path)
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        print(f"{p}:{e.lineno}:{e.msg}")
        return 1
    errors: list[str] = []
    for idx, node in enumerate(data.get("nodes", []), start=1):
        if "id" not in node:
            errors.append(f"nodes[{idx}] missing 'id'")
        if "type" not in node:
            errors.append(f"nodes[{idx}] missing 'type'")
    if errors:
        print("validation errors:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("flow valid")
    return 0


def flow_augment(path: str) -> None:
    """Inject basic error handlers into a flow JSON file."""
    p = Path(path)
    data = json.loads(p.read_text())
    for node in data.get("nodes", []):
        node.setdefault(
            "errorHandler",
            {
                "maxRetries": 3,
                "backoffMs": 1000,
                "onError": "notify Slack",
                "deadLetter": True,
            },
        )
    p.write_text(json.dumps(data, indent=2))
    print(f"augmented flow written to {p}")


def instrument_code(path: str) -> None:
    """Insert span helpers into a source file."""
    p = Path(path)
    lines = p.read_text().splitlines()
    import_line = 'import { startSpan, endSpan } from "telemetry";'
    if import_line not in lines:
        lines.insert(0, import_line)
    p.write_text("\n".join(lines) + "\n")
    print(f"instrumented {p}")


def secure_plugin(name: str, scopes: Iterable[str]) -> None:
    """Update plugin manifest and central policies with scopes."""
    plugin_dir = Path("plugins") / name
    manifest_path = plugin_dir / "plugin.json"
    if not manifest_path.exists():
        print(f"plugin {name} not found")
        return
    manifest = json.loads(manifest_path.read_text())
    manifest.setdefault("scopes", [])
    for scope in scopes:
        if scope not in manifest["scopes"]:
            manifest["scopes"].append(scope)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    policy_path = Path("policies.json")
    if policy_path.exists():
        policy = json.loads(policy_path.read_text())
    else:
        policy = {}
    policy.setdefault(name, {"scopes": []})
    for scope in scopes:
        if scope not in policy[name]["scopes"]:
            policy[name]["scopes"].append(scope)
    policy_path.write_text(json.dumps(policy, indent=2))
    print(f"updated scopes for {name}")


def generate_tests(path: str, framework: str) -> None:
    """Generate a minimal test file for a plugin endpoint."""
    p = Path(path)
    test_dir = p.parent / "__tests__"
    test_dir.mkdir(exist_ok=True)
    if framework == "jest":
        test_file = test_dir / f"{p.stem}.test.ts"
        content = (
            f"import {{ handler }} from '../{p.name}';\n\n"
            "test('handler succeeds', async () => {\n"
            "  const res = await handler();\n"
            "  expect(res).toBeDefined();\n"
            "});\n"
        )
    else:
        test_file = test_dir / f"test_{p.stem}.py"
        content = (
            f"from ..{p.stem} import handler\n\n"
            "def test_handler_succeeds():\n"
            "    assert handler() is not None\n"
        )
    test_file.write_text(content)
    print(f"generated test at {test_file}")


def release_prep(release_type: str) -> None:
    """Placeholder release preparation step."""
    print(f"Preparing {release_type} release (format, lint, tag)")
