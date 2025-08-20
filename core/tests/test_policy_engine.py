import os
import sys
import time
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from agent_mono import policy
from tools.builtin.fs import fs_write_text
from tools.builtin.fs_read import fs_read
from tools.builtin.http import http_fetch_text


def write_policy(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")
    os.utime(p, None)


def test_policy_schema_validation_fails_on_extra_brace(tmp_path, monkeypatch):
    p = tmp_path / "policies.json"
    p.write_text('{"capabilities": {}}}', encoding="utf-8")
    monkeypatch.setattr(policy, "_PATH", p)
    policy._MTIME = 0
    with pytest.raises(policy.PolicyError):
        policy._reload_if_needed()


def test_unknown_capability_is_denied(tmp_path, monkeypatch):
    p = tmp_path / "policies.json"
    write_policy(
        p,
        '{"capabilities":{"fs.read":{"default":"deny"},"fs.write":{"default":"deny"},"network":{"default":"deny"},"subprocess":{"default":"deny"}}}',
    )
    monkeypatch.setattr(policy, "_PATH", p)
    policy._MTIME = 0
    policy._reload_if_needed()
    with pytest.raises(PermissionError):
        policy.check("unknown")


def test_fs_read_denied_by_default_then_allowed_when_policy_changes(tmp_path, monkeypatch):
    file = tmp_path / "data.txt"
    file.write_text("hi", encoding="utf-8")
    p = tmp_path / "policies.json"
    deny = (
        '{"capabilities":{"fs.read":{"default":"deny"},"fs.write":{"default":"deny"},"network":{"default":"deny"},"subprocess":{"default":"deny"}}}'
    )
    allow = (
        '{"capabilities":{"fs.read":{"default":"allow"},"fs.write":{"default":"deny"},"network":{"default":"deny"},"subprocess":{"default":"deny"}}}'
    )
    write_policy(p, deny)
    monkeypatch.setattr(policy, "_PATH", p)
    policy._MTIME = 0
    with pytest.raises(PermissionError):
        fs_read(file)
    time.sleep(1)
    write_policy(p, allow)
    assert fs_read(file)["success"]


def test_policy_hot_reload_atomic_swap(tmp_path, monkeypatch):
    file = tmp_path / "data.txt"
    file.write_text("hi", encoding="utf-8")
    p = tmp_path / "policies.json"
    good = (
        '{"capabilities":{"fs.read":{"default":"allow"},"fs.write":{"default":"deny"},"network":{"default":"deny"},"subprocess":{"default":"deny"}}}'
    )
    write_policy(p, good)
    monkeypatch.setattr(policy, "_PATH", p)
    policy._MTIME = 0
    assert fs_read(file)["success"]
    bad = good + "}"
    write_policy(p, bad)
    assert fs_read(file)["success"]


def test_cli_refuses_planning_input_when_planner_missing():
    proc = subprocess.run(
        [sys.executable, "-m", "agent_mono.cli", "do this and then that"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "Planning is not implemented" in (proc.stderr + proc.stdout)


def test_fs_write_diff_suppressed_for_large_files(tmp_path, monkeypatch):
    p = tmp_path / "policies.json"
    policy_text = (
        '{"capabilities":{"fs.read":{"default":"deny"},"fs.write":{"default":"allow","allowed_paths":["'
        + str(tmp_path)
        + '" ]},"network":{"default":"deny"},"subprocess":{"default":"deny"}}}'
    )
    write_policy(p, policy_text)
    monkeypatch.setattr(policy, "_PATH", p)
    policy._MTIME = 0
    big_content = "a" * (200_000)
    path = tmp_path / "big.txt"
    res = fs_write_text(path, big_content)
    assert res["diff"] == "<diff suppressed>"


def test_http_respects_max_bytes_and_content_type_list(tmp_path, monkeypatch):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/xml":
                ct = "application/xml"
            else:
                ct = "text/plain"
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.end_headers()
            self.wfile.write(b"hello world")

    server = HTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    p = tmp_path / "policies.json"
    policy_text = (
        '{"capabilities":{"fs.read":{"default":"deny"},"fs.write":{"default":"deny"},"network":{"default":"allow"},"subprocess":{"default":"deny"}}}'
    )
    write_policy(p, policy_text)
    monkeypatch.setattr(policy, "_PATH", p)
    policy._MTIME = 0
    res = http_fetch_text(base + "/ok", max_bytes=5)
    assert not res["success"]
    monkeypatch.setenv("HTTP_ALLOWED_CONTENT_TYPES", "text/")
    res2 = http_fetch_text(base + "/xml")
    assert not res2["success"]
    server.shutdown()
    thread.join()

