"""Run the CLI smoke, applying a resource envelope on supported Linux hosts only."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDRESS_SPACE_LIMIT_MIB = 1536
REQUIRED_MARKERS = (
    "IA_FARM_MOCK=1",
    "Demonstração concluída",
    "Encerrando a simulação",
)


def _missing_markers(output: str) -> list[str]:
    return [marker for marker in REQUIRED_MARKERS if marker not in output]


def main() -> int:
    environment = os.environ.copy()
    environment.update({
        "IA_FARM_MOCK": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "PYTHONIOENCODING": "utf-8:replace",
        "TERM": "dumb",
    })

    cpu_id = None
    process_limits = None
    profile_description = "platform smoke; no CPU or memory envelope"
    if os.name == "posix" and hasattr(os, "sched_getaffinity"):
        import resource

        available_cpus = sorted(os.sched_getaffinity(0))
        if available_cpus and hasattr(resource, "RLIMIT_AS"):
            cpu_id = available_cpus[0]
            address_space_limit = ADDRESS_SPACE_LIMIT_MIB * 1024 * 1024

            def apply_process_limits() -> None:
                os.sched_setaffinity(0, {cpu_id})
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (address_space_limit, address_space_limit),
                )

            process_limits = apply_process_limits
            profile_description = (
                f"one logical CPU (CPU {cpu_id}); {ADDRESS_SPACE_LIMIT_MIB} MiB "
                "virtual-address-space limit"
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
            check=False,
            **({"preexec_fn": process_limits} if process_limits else {}),
        )
    except subprocess.TimeoutExpired:
        print("FAIL: app did not finish the startup/demo/exit smoke within 30 seconds.")
        return 1

    output = result.stdout + result.stderr
    missing = _missing_markers(output)
    print(f"SMOKE PROFILE: {profile_description}; offline; mock retrieval; generative model disabled")
    if result.returncode or missing:
        print("Captured output (escaped for the current terminal encoding):")
        print(output.encode("ascii", errors="backslashreplace").decode("ascii"))
        print(f"FAIL: exit={result.returncode}; missing markers={missing}")
        return 1

    print("PASS: app started, ran the demo interactions, and shut down cleanly.")
    print("LIMIT: platform startup/CLI smoke only; not an Android or ARM64 benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
