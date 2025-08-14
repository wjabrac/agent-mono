import json
import subprocess
from pathlib import Path


def run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    script = Path(__file__).resolve().parents[2] / "tools" / "agent_cli.py"
    cmd = ["python", str(script), *args, "--root", str(tmp_path)]
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def test_create_plugin(tmp_path: Path):
    run_cli(tmp_path, "create", "plugin", "demo")
    plugin_dir = tmp_path / "plugins" / "demo"
    assert (plugin_dir / "plugin.json").exists()
    with open(plugin_dir / "plugin.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["name"] == "demo"
    assert (plugin_dir / "demo.py").exists()


def test_create_service(tmp_path: Path):
    run_cli(tmp_path, "create", "service", "demo_service")
    service_dir = tmp_path / "services" / "demo_service"
    assert (service_dir / "main.py").exists()

