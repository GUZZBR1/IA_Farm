"""Dependency diagnostic for local setup."""

import importlib.util


REQUIRED_MODULES = ("numpy", "faiss", "sentence_transformers", "requests", "yaml", "psutil")


def main() -> int:
    missing = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    if missing:
        print("Missing dependencies:", ", ".join(missing))
        return 1
    print("All runtime dependencies are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
