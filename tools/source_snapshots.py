"""Content-addressed source snapshots and stable evidence locator contracts.

Snapshot bytes are stored outside Git by default. The returned manifest is safe
to retain in the repository, but a hash proves integrity only, not correctness.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

LICENSE_STATUSES = frozenset({
    "UNKNOWN", "LINK_ONLY", "REDISTRIBUTION_ALLOWED", "ATTRIBUTION_REQUIRED",
    "RESTRICTED", "PUBLIC_DOMAIN",
})
LOCATOR_KINDS = frozenset({
    "page", "section", "table", "figure", "paragraph", "heading",
    "document_fragment",
})
_SOURCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate_locator(locator: Any) -> None:
    """Validate a structured, snapshot-relative locator (never a bare quote)."""
    if not isinstance(locator, dict) or not locator:
        raise ValueError("locator must be a non-empty object")
    if set(locator) - (LOCATOR_KINDS | {"page_start", "page_end", "quote_hash"}):
        raise ValueError("locator contains unsupported fields")
    concrete = [key for key in LOCATOR_KINDS if key in locator]
    if not concrete and not ({"page_start", "page_end"} & set(locator)):
        raise ValueError("locator must identify a page, section, table, figure, paragraph, heading, or fragment")
    for key in concrete:
        if not isinstance(locator[key], (str, int)) or isinstance(locator[key], bool) or not str(locator[key]).strip():
            raise ValueError(f"locator.{key} must be non-empty text or an integer")
    for key in ("page_start", "page_end"):
        if key in locator and (type(locator[key]) is not int or locator[key] < 1):
            raise ValueError(f"locator.{key} must be a positive integer")
    if ("page_start" in locator and "page_end" in locator
            and locator["page_end"] < locator["page_start"]):
        raise ValueError("page_end cannot precede page_start")
    if "quote_hash" in locator and not _SHA256.fullmatch(str(locator["quote_hash"])):
        raise ValueError("locator.quote_hash must be a lowercase SHA-256")


def validate_license_status(status: Any) -> None:
    if not isinstance(status, str) or status not in LICENSE_STATUSES:
        raise ValueError("unknown license status")


def capture_snapshot(*, source_id: str, original_url: str, content: bytes,
                     mime_type: str, document_title: str, institution: str,
                     license_status: str = "UNKNOWN", publication_date: str | None = None,
                     document_version: str | None = None,
                     retrieved_at: str | None = None,
                     storage_root: Path) -> dict[str, Any]:
    """Write immutable bytes and metadata keyed by their digest.

    Re-capturing identical bytes is idempotent. Changed bytes create a new
    snapshot and are explicitly marked as changed from the most recent one.
    """
    if not _SOURCE_ID.fullmatch(source_id):
        raise ValueError("source_id contains unsafe path characters")
    parsed = urlsplit(original_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("original_url must be a credential-free HTTPS URL")
    for field, value in (("mime_type", mime_type), ("document_title", document_title), ("institution", institution)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
    validate_license_status(license_status)
    timestamp = retrieved_at or datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError
    except ValueError as exc:
        raise ValueError("retrieved_at must be a timezone-aware ISO timestamp") from exc
    if not isinstance(content, bytes) or not content:
        raise ValueError("snapshot content must be non-empty bytes")
    digest = hashlib.sha256(content).hexdigest()
    root = Path(storage_root).resolve()
    source_dir = root / source_id
    source_dir.mkdir(parents=True, exist_ok=True)
    blob = source_dir / f"{digest}.blob"
    if blob.exists():
        if hashlib.sha256(blob.read_bytes()).hexdigest() != digest:
            raise ValueError("existing content-addressed snapshot is corrupted")
    else:
        with blob.open("xb") as handle:
            handle.write(content)
    manifest_path = source_dir / f"{digest}.json"
    previous = sorted(source_dir.glob("*.json"))
    previous_hashes = [p.stem for p in previous if p.stem != digest and _SHA256.fullmatch(p.stem)]
    metadata = {
        "snapshot_id": f"{source_id}:{digest}", "source_id": source_id,
        "original_url": original_url, "retrieved_at": timestamp,
        "content_hash": digest, "mime_type": mime_type,
        "file_size": len(content), "document_title": document_title,
        "institution": institution, "publication_date": publication_date,
        "document_version": document_version, "license_status": license_status,
        "local_path": str(blob.relative_to(root)).replace("\\", "/"),
        "snapshot_status": ("CHANGED_SINCE_PRIOR_SNAPSHOT"
                            if previous_hashes and not manifest_path.exists() else "CAPTURED"),
        "previous_snapshot_hashes": previous_hashes,
    }
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if {**existing, "retrieved_at": timestamp} != metadata:
            # Keep the first capture timestamp for an identical immutable object.
            comparable = dict(metadata)
            comparable["retrieved_at"] = existing.get("retrieved_at")
            if comparable != existing:
                raise ValueError("snapshot manifest is immutable and does not match capture metadata")
        return existing
    manifest_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metadata


def verify_snapshot(snapshot: dict[str, Any], *, storage_root: Path) -> bool:
    """Return true only when referenced bytes exist and match the manifest hash."""
    digest = snapshot.get("content_hash")
    relative = snapshot.get("local_path")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest) or not isinstance(relative, str):
        return False
    root = Path(storage_root).resolve()
    path = (root / relative).resolve()
    if root not in path.parents:
        return False
    try:
        content = path.read_bytes()
    except OSError:
        return False
    return len(content) == snapshot.get("file_size") and hashlib.sha256(content).hexdigest() == digest


def write_public_manifest(snapshot: dict[str, Any], *, manifest_root: Path) -> Path:
    """Write one immutable, source-safe metadata manifest for repository review."""
    source_id = snapshot.get("source_id")
    digest = snapshot.get("content_hash")
    if not isinstance(source_id, str) or not _SOURCE_ID.fullmatch(source_id):
        raise ValueError("manifest source_id is invalid")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ValueError("manifest content_hash is invalid")
    directory = Path(manifest_root) / source_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{digest}.json"
    encoded = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != encoded:
            old = json.loads(path.read_text(encoding="utf-8"))
            # Preserve the first retrieval timestamp for identical content.
            if {**snapshot, "retrieved_at": old.get("retrieved_at")} != old:
                raise ValueError("public source manifest is immutable")
        return path
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(encoded)
    return path


def source_changed(snapshot: dict[str, Any], new_content: bytes) -> bool:
    """Compare newly acquired bytes against a frozen snapshot digest."""
    return hashlib.sha256(new_content).hexdigest() != snapshot.get("content_hash")
