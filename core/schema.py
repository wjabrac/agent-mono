from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Manifest:
    name: str
    version: str
    scopes_allow: list[str]
    rate_limit_per_min: int
    network: str
    working_dir: str


REQUIRED_FIELDS = {
    "name",
    "version",
    "scopes_allow",
    "rate_limit_per_min",
    "network",
    "working_dir",
}


def validate_manifest(path: Path) -> Manifest:
    """Validate plugin.json and return a Manifest.

    Unknown or missing fields cause validation failure.
    """
    data = json.loads(Path(path).read_text())
    if set(data.keys()) != REQUIRED_FIELDS:
        raise ValueError("Unknown or missing fields in manifest")
    if not isinstance(data["scopes_allow"], list):
        raise ValueError("scopes_allow must be a list")
    return Manifest(
        name=str(data["name"]),
        version=str(data["version"]),
        scopes_allow=[str(s) for s in data["scopes_allow"]],
        rate_limit_per_min=int(data["rate_limit_per_min"]),
        network=str(data["network"]),
        working_dir=str(data["working_dir"]),
    )
