"""Scan tracked source files for credentials and stale machine-specific paths."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PATTERNS = (
    ("OpenRouter-style credential", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("hardcoded OpenRouter key", re.compile(r"OPENROUTER_API_KEY\s*=\s*[\"'][^\"']+[\"']")),
    ("developer-specific path", re.compile(r"/home/guzzbr|/home/guzzbr|/src/")),
    ("obsolete miner path", re.compile(r"scripts/miner\.py")),
)


def tracked_files(root: Path) -> list[Path]:
    output = subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"], text=False
    )
    return [root / item for item in output.decode().split("\0") if item]


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in tracked_files(root):
        # This file necessarily contains the detection signatures themselves.
        if path.resolve() == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{path.relative_to(root)}:{line}: {label}")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    findings = scan(root)
    if findings:
        print("Security scan failed:")
        print("\n".join(findings))
        return 1
    print("Security scan passed: no active credential or stale-path findings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
