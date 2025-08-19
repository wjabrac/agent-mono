from pathlib import Path
import pytest

from tools.builtin.fs import fs_write_text


def test_fs_write_denied(tmp_path):
    target = tmp_path / "x.txt"
    with pytest.raises(PermissionError):
        fs_write_text(target, "hi")
