import subprocess


def run_shell(argv: list[str], timeout: float = 10.0):
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return {
        "success": proc.returncode == 0,
        "code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
