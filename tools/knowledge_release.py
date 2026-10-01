"""Build an immutable release manifest from canonical published records."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from tools.curation_registry import CurationRegistry, PROJECT_ROOT
from tools.knowledge_schema import validate_record

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STORE = ROOT / "data" / "knowledge_base" / "approved_records.json"
APPROVAL_POLICY_VERSION = "human-source-snapshot-v1"
DEFAULT_REGISTRY = ROOT / "data" / "curation_registry.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_published_authority(records: list[dict[str, Any]], registry_path: Path,
                                 base_dir: Path = PROJECT_ROOT) -> None:
    """Require a separately validated registry entry for every published record."""
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise ValueError("curation registry is malformed")
    by_id = {entry.get("record_id"): entry for entry in entries if isinstance(entry, dict)}
    if len(by_id) != len(entries):
        raise ValueError("curation registry has missing or duplicate record IDs")
    registry = CurationRegistry(path=registry_path, base_dir=base_dir)
    for record in records:
        entry = by_id.get(record.get("record_id"))
        approval = record.get("approval")
        if not entry or not isinstance(approval, dict):
            raise ValueError("published record has no independent curation registry entry")
        if (approval.get("review_entry_sha256") != hashlib.sha256(
                json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()):
            raise ValueError("record approval does not bind the exact external curation entry")
        if (approval.get("review_id") != entry.get("review_id")
                or approval.get("reviewer_ids") != entry.get("reviewer_ids")
                or approval.get("approver_id") != entry.get("approver_id")
                or approval.get("approver_type") != "human"
                or approval.get("content_sha256") != entry.get("approved_content_sha256")):
            raise ValueError("record approval identities do not match the external curation entry")
        if not any(source.get("source_id") == entry.get("source_id") for source in record["sources"]):
            raise ValueError("published record does not include the approved excerpt source")
        if len(record["sources"]) != 1 or record["sources"][0].get("source_id") != entry.get("source_id"):
            raise ValueError("current curation contract authorizes exactly one source per published record")
        snapshot = next((item for item in entry["source_snapshots"]
                         if item.get("source_id") == entry.get("source_id")), None)
        source = record["sources"][0]
        if (snapshot is None or source.get("snapshot_ref") != snapshot.get("path")
                or source.get("snapshot_sha256") != snapshot.get("sha256")):
            raise ValueError("published source snapshot does not match the externally reviewed snapshot")
        frozen_path = Path(entry["review_input"]["path"])
        frozen_path = frozen_path if frozen_path.is_absolute() else base_dir / frozen_path
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        candidate = next((item for item in frozen.get("cases", [])
                          if item.get("id") == entry.get("review_id")), None)
        if candidate is None or candidate.get("context") != record.get("scope"):
            raise ValueError("published record scope differs from the exact frozen review context")
        expected_source = next((item for item in frozen.get("sources", [])
                                if item.get("id") == entry.get("source_id")), None)
        if (expected_source is None or source.get("url") != expected_source.get("url")
                or source.get("title") != expected_source.get("title", source.get("title"))):
            raise ValueError("published source URL/title does not match the frozen candidate source")
        excerpt = {"text": record["text"], "metadata": {
            "curation_record_id": record["record_id"], "source_id": entry.get("source_id"),
            "review_status": "approved", "crop": record["scope"].get("crop"),
            "review_date": approval.get("reviewed_at"), "reviewed_at": approval.get("reviewed_at"),
            "review_input_sha256": entry["review_input"]["sha256"],
            **{key: value for key, value in record["scope"].items() if key != "crop"},
        }}
        if not registry.authorizes(excerpt):
            raise ValueError("published record is not authorized by the validated runtime curation registry")


def build_manifest(records: list[dict[str, Any]], *, index_version: str = "none",
                   created_at: str | None = None, registry_path: Path = DEFAULT_REGISTRY,
                   base_dir: Path = PROJECT_ROOT) -> dict[str, Any]:
    if not isinstance(records, list) or not records:
        raise ValueError("cannot publish a release with an empty approved knowledge store")
    for record in records:
        validate_record(record)
        if record["status"] != "PUBLISHED":
            raise ValueError("release store may contain only PUBLISHED records")
    validate_published_authority(records, registry_path, base_dir)
    ids = [record["record_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("published record IDs must be unique")
    ordered = sorted(records, key=lambda record: record["record_id"])
    canonical = json.dumps(ordered, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sources = sorted({source["source_id"] for record in ordered for source in record["sources"]})
    return {
        "manifest_schema_version": 1,
        "knowledge_release_id": f"kr-{uuid4()}",
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "schema_version": ordered[0]["schema_version"],
        "knowledge_base_version": sha256_bytes(canonical),
        "corpus_version": sha256_bytes(canonical),
        "record_count": len(ordered),
        "records_hash": sha256_bytes(canonical),
        "source_set": sources,
        "index_version": index_version,
        "approval_policy_version": APPROVAL_POLICY_VERSION,
    }


def load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported canonical knowledge store schema")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("knowledge store must contain a records array")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--index-version", default="none")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    manifest = build_manifest(load_records(args.store), index_version=args.index_version,
                              registry_path=args.registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Published manifest {manifest['knowledge_release_id']} ({manifest['record_count']} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
