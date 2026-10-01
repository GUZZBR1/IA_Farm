"""Report vector-runtime prerequisites without installing or downloading anything."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys

from tools.retrieval_runtime import detect_vector_capability


def diagnose(*, model_path: Path | None, index_path: Path | None) -> dict:
    try:
        socket.getaddrinfo("pypi.org", 443, type=socket.SOCK_STREAM)
        pypi_dns = "AVAILABLE"
    except OSError:
        pypi_dns = "UNAVAILABLE"
    pip_version = subprocess.run([sys.executable, "-m", "pip", "--version"],
                                 capture_output=True, text=True, check=False)
    pip_check = subprocess.run([sys.executable, "-m", "pip", "check"],
                               capture_output=True, text=True, check=False)
    disk = shutil.disk_usage(Path.cwd())
    return {
        "capability": detect_vector_capability(model_path=model_path, index_path=index_path),
        "pypi_dns": pypi_dns,
        "pip_version": pip_version.stdout.strip() if pip_version.returncode == 0 else None,
        "pip_check_exit_code": pip_check.returncode,
        "pip_check_output": (pip_check.stdout + pip_check.stderr).strip(),
        "working_volume_free_bytes": disk.free,
        "requirements_profiles": {
            "core": str(Path("requirements-core.txt")),
            "vector_direct_inputs": str(Path("requirements-vector.in")),
            "transitive_lock": "not_generated",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--index", type=Path)
    args = parser.parse_args()
    print(json.dumps(diagnose(model_path=args.model, index_path=args.index), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
