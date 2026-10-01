"""Explicit vector-runtime capabilities and index/embedding compatibility."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
from typing import Any

CAPABILITY_STATES = frozenset({
    "AVAILABLE", "DEPENDENCY_MISSING", "MODEL_MISSING", "INDEX_MISSING",
    "INDEX_INVALID", "UNSUPPORTED_PLATFORM",
})
MANIFEST_NAME = "index_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def detect_vector_capability(*, model_path: Path | None = None,
                             index_path: Path | None = None) -> dict[str, Any]:
    """Probe without downloading packages, models, or indexes."""
    architecture = platform.machine().lower()
    system = platform.system().lower()
    platform_supported = (
        architecture in {"x86_64", "amd64"} and system in {"linux", "windows", "darwin"}
    ) or (architecture in {"aarch64", "arm64"} and system == "darwin")
    modules = {}
    for name, import_name in (("numpy", "numpy"), ("faiss", "faiss"),
                              ("sentence_transformers", "sentence_transformers")):
        try:
            module = __import__(import_name)
            modules[name] = {"available": True, "version": getattr(module, "__version__", None)}
        except (ImportError, OSError) as exc:
            modules[name] = {"available": False, "error_type": type(exc).__name__}
    model_exists = bool(model_path and Path(model_path).is_dir())
    index_exists = bool(index_path and (Path(index_path) / MANIFEST_NAME).is_file())
    if not platform_supported:
        state = "UNSUPPORTED_PLATFORM"
    elif not all(item["available"] for item in modules.values()):
        state = "DEPENDENCY_MISSING"
    elif not model_exists:
        state = "MODEL_MISSING"
    elif not index_exists:
        state = "INDEX_MISSING"
    else:
        try:
            validate_index_manifest(Path(index_path),
                                    expected_release=None,
                                    expected_model_path=Path(model_path))
            state = "AVAILABLE"
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError):
            state = "INDEX_INVALID"
    return {
        "state": state, "python": sys.version.split()[0],
        "platform": platform.platform(), "architecture": platform.machine(),
        "platform_supported_by_probe": platform_supported,
        "dependencies": modules, "model_path": str(model_path) if model_path else None,
        "model_available_locally": model_exists,
        "index_path": str(index_path) if index_path else None,
        "index_manifest_available": index_exists,
        "automatic_downloads": False,
    }


def embedding_artifact_hash(model_path: Path) -> str:
    """Hash local model file inventory and contents in deterministic path order."""
    root = Path(model_path).resolve()
    if not root.is_dir():
        raise ValueError("model directory is missing")
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise ValueError("model directory is empty")
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(bytes.fromhex(_sha256(path)))
    return digest.hexdigest()


def validate_embedding_manifest(manifest: Any, model_path: Path) -> dict[str, Any]:
    required = {"model_id", "revision", "expected_dimension", "artifact_origin", "artifact_hash"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValueError("embedding model manifest schema is invalid")
    if any(not isinstance(manifest[key], str) or not manifest[key].strip()
           for key in ("model_id", "revision", "artifact_origin")):
        raise ValueError("embedding model identity/revision/origin must be explicit")
    if type(manifest["expected_dimension"]) is not int or manifest["expected_dimension"] <= 0:
        raise ValueError("embedding expected_dimension must be a positive integer")
    if not isinstance(manifest["artifact_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", manifest["artifact_hash"]):
        raise ValueError("embedding artifact_hash must be SHA-256")
    if embedding_artifact_hash(Path(model_path)) != manifest["artifact_hash"]:
        raise ValueError("local embedding files differ from the declared model artifact hash")
    return manifest


def build_index_manifest(*, index_path: Path, index_type: str,
                         embedding_model: dict[str, Any], knowledge_release: str,
                         record_count: int, dimension: int) -> dict[str, Any]:
    """Create the compatibility sidecar after FAISS files have been written."""
    root = Path(index_path)
    faiss_file = root / "faiss.index"
    metadata_file = root / "metadata.json"
    if not faiss_file.is_file() or not metadata_file.is_file():
        raise ValueError("index files are missing")
    required_model_fields = {"model_id", "revision", "expected_dimension", "artifact_origin", "artifact_hash"}
    if not isinstance(embedding_model, dict) or not required_model_fields <= embedding_model.keys():
        raise ValueError("embedding model manifest lacks pinned identity/artifact fields")
    if embedding_model["expected_dimension"] != dimension or not isinstance(dimension, int) or dimension <= 0:
        raise ValueError("embedding model dimension does not match the built index")
    artifact_hash = embedding_model["artifact_hash"]
    if not isinstance(artifact_hash, str) or len(artifact_hash) != 64:
        raise ValueError("embedding artifact_hash must be SHA-256")
    return {
        "manifest_schema_version": 1, "index_type": index_type,
        "embedding_model": embedding_model["model_id"],
        "embedding_revision": embedding_model["revision"],
        "embedding_dimension": dimension,
        "embedding_artifact_hash": artifact_hash,
        "embedding_artifact_origin": embedding_model["artifact_origin"],
        "knowledge_release": knowledge_release, "record_count": record_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "index_files": {
            "faiss.index": {"sha256": _sha256(faiss_file), "size": faiss_file.stat().st_size},
            "metadata.json": {"sha256": _sha256(metadata_file), "size": metadata_file.stat().st_size},
        },
    }


def validate_index_manifest(index_path: Path, *, expected_release: str | None,
                            expected_model_path: Path | None = None,
                            expected_model: str | None = None,
                            expected_revision: str | None = None,
                            expected_dimension: int | None = None) -> dict[str, Any]:
    root = Path(index_path)
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    required = {"manifest_schema_version", "index_type", "embedding_model", "embedding_revision",
                "embedding_dimension", "embedding_artifact_hash", "embedding_artifact_origin",
                "knowledge_release", "record_count", "created_at", "index_files"}
    if not isinstance(manifest, dict) or not required <= manifest.keys() or manifest["manifest_schema_version"] != 1:
        raise ValueError("invalid index manifest schema")
    if expected_release is not None and manifest["knowledge_release"] != expected_release:
        raise ValueError("knowledge release mismatch")
    if expected_model is not None and manifest["embedding_model"] != expected_model:
        raise ValueError("embedding model mismatch")
    if expected_revision is not None and manifest["embedding_revision"] != expected_revision:
        raise ValueError("embedding revision mismatch")
    if expected_dimension is not None and manifest["embedding_dimension"] != expected_dimension:
        raise ValueError("embedding dimension mismatch")
    for name in ("faiss.index", "metadata.json"):
        path = root / name
        expected = manifest["index_files"].get(name)
        if not path.is_file() or not isinstance(expected, dict) or _sha256(path) != expected.get("sha256"):
            raise ValueError(f"index file hash mismatch: {name}")
        if path.stat().st_size != expected.get("size"):
            raise ValueError(f"index file size mismatch: {name}")
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, list) or len(metadata) != manifest["record_count"]:
        raise ValueError("record count does not match index metadata")
    if expected_model_path is not None:
        if embedding_artifact_hash(expected_model_path) != manifest["embedding_artifact_hash"]:
            raise ValueError("embedding model artifact hash mismatch")
    return manifest
