from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


class Sandbox:
    def __init__(self) -> None:
        self.path = Path(tempfile.mkdtemp())

    def resolve(self, rel: str) -> Path:
        p = (self.path / rel).resolve()
        if not str(p).startswith(str(self.path)):
            raise PermissionError("path traversal outside sandbox")
        cur = self.path
        for part in Path(rel).parts:
            cur = cur / part
            if cur.is_symlink():
                raise PermissionError("symlinks not allowed")
        return p

    def cleanup(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)
