"""Launch the app under a small Linux/WSL process envelope (not Android)."""

from __future__ import annotations

import os
from pathlib import Path
import resource
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDRESS_SPACE_LIMIT_MIB = 1536


def main() -> int:
    if not hasattr(os, "sched_getaffinity") or not hasattr(resource, "RLIMIT_AS"):
        print("This smoke profile requires Linux/WSL CPU affinity and RLIMIT_AS support.")
        return 2

    available_cpus = sorted(os.sched_getaffinity(0))
    if not available_cpus:
        print("No available CPU could be assigned to the smoke process.")
        return 2

    cpu_id = available_cpus[0]
    address_space_limit = ADDRESS_SPACE_LIMIT_MIB * 1024 * 1024
    environment = os.environ.copy()
    environment.update({
        "IA_FARM_MOCK": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TERM": "dumb",
    })

    def apply_process_limits() -> None:
        os.sched_setaffinity(0, {cpu_id})
        resource.setrlimit(
            resource.RLIMIT_AS,
            (address_space_limit, address_space_limit),
        )

    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "main.py")],
            input="demo\nexit\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            cwd=PROJECT_ROOT,
            timeout=30,
            preexec_fn=apply_process_limits,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print("FAIL: app did not finish the startup/demo/exit smoke within 30 seconds.")
        return 1

    output = result.stdout + result.stderr
    required_markers = (
        "IA_FARM_MOCK=1",
        "Unified Simulation Interface",
        "Demo Completed",
        "Shutting down simulation",
    )
    missing = [marker for marker in required_markers if marker not in output]
    print(output, end="")
    print(
        f"\nSMOKE PROFILE: one logical CPU (CPU {cpu_id}); "
        f"{ADDRESS_SPACE_LIMIT_MIB} MiB virtual-address-space limit; offline; "
        "mock retrieval; generative model disabled"
    )
    if result.returncode or missing:
        print(f"FAIL: exit={result.returncode}; missing markers={missing}")
        return 1

    print("PASS: app started, ran the demo interactions, and shut down cleanly.")
    print("LIMIT: Linux/WSL x86_64 smoke only; not an Android or ARM64 benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
