import subprocess
import sys
from pathlib import Path


def test_build_and_install(tmp_path):
    subprocess.run([sys.executable, "-m", "pip", "install", "build"], check=True, stdout=subprocess.DEVNULL)
    dist = tmp_path / "dist"
    subprocess.run([sys.executable, "-m", "build", "--wheel", "--sdist", "--outdir", str(dist)], check=True)
    wheel = next(dist.glob("*.whl"))
    subprocess.run([sys.executable, "-m", "venv", str(tmp_path / "venv")], check=True)
    pip = tmp_path / "venv" / "bin" / "pip"
    agent = tmp_path / "venv" / "bin" / "agent"
    subprocess.run([str(pip), "install", f"{wheel}[http]"], check=True)
    proc = subprocess.run([str(agent), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
