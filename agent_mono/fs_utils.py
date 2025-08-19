from pathlib import Path
import os, tempfile


def write_text_atomic(path: Path, content: str, encoding: str = "utf-8") -> None:
    d = path.parent
    d.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(d), encoding=encoding) as f:
        tmp = Path(f.name)
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
