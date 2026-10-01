"""Fail-closed runtime allowlist for exact, reviewed source excerpts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from datetime import date
from typing import Any

from tools.review_verifier import compare_reviews

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_SCHEMA_VERSION = 2


def _artifact(path_value: str, expected_sha256: str, base_dir: Path) -> Path:
    path = Path(path_value)
    path = path if path.is_absolute() else base_dir / path
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError(f"curation artifact missing or hash mismatch: {path_value}")
    return path


def validate_entry(entry: dict[str, Any], base_dir: Path = PROJECT_ROOT) -> None:
    """Verify ingested source bytes, exact text, AI evidence, and human approval."""
    required = (
        "record_id", "review_id", "text_sha256", "source_id", "crop",
        "review_date", "review_input", "review_artifacts", "comparison_artifact",
        "source_snapshots", "human_approval", "reviewer_ids", "approver_id", "approver_type",
        "approved_content_sha256",
    )
    if any(not entry.get(field) for field in required):
        raise ValueError("curation entry is missing required provenance fields")
    if (entry["approver_type"] != "human" or not isinstance(entry["approver_id"], str)
            or not entry["approver_id"].strip()
            or entry["reviewer_ids"] != ["maize_evidence_specialist", "independent_verifier"]
            or entry["approver_id"].strip().casefold() in {
                reviewer.casefold() for reviewer in entry["reviewer_ids"]
            }):
        raise ValueError("curation entry requires two named AI reviews and a distinct human approver")
    frozen = entry["review_input"]
    input_path = _artifact(frozen["path"], frozen["sha256"], base_dir)
    if not re.fullmatch(r"[0-9a-f]{64}", entry["text_sha256"]):
        raise ValueError("text_sha256 must be a lowercase SHA-256")
    candidate_set = json.loads(input_path.read_text(encoding="utf-8"))
    candidate = next((item for item in candidate_set.get("cases", [])
                      if item.get("id") == entry["review_id"]), None)
    if (not candidate or entry["source_id"] not in candidate.get("source_ids", [])
            or candidate.get("context", {}).get("crop") != entry["crop"]):
        raise ValueError("record source/crop does not match the frozen reviewed case")
    if not isinstance(candidate.get("context"), dict) or not candidate["context"]:
        raise ValueError("curation approval must bind a non-empty reviewed scope")
    known_sources = {
        item.get("id"): item.get("url")
        for item in candidate_set.get("sources", []) if isinstance(item, dict)
    }
    expected_urls = {known_sources.get(source_id) for source_id in candidate["source_ids"]}
    snapshots = entry["source_snapshots"]
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError("curation approval must bind at least one ingested source snapshot")
    snapshot_map: dict[str, tuple[Path, str]] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or not all(
            isinstance(snapshot.get(field), str) and snapshot[field].strip()
            for field in ("source_id", "path", "sha256")
        ):
            raise ValueError("source snapshots require source_id, path, and sha256")
        source_id = snapshot["source_id"]
        source_path = _artifact(snapshot["path"], snapshot["sha256"], base_dir)
        if source_id not in candidate.get("source_ids", []) or source_id in snapshot_map:
            raise ValueError("source snapshot must uniquely bind a frozen candidate source")
        snapshot_map[source_id] = (source_path, snapshot["sha256"])
    if entry["source_id"] not in snapshot_map:
        raise ValueError("approved excerpt source must have an ingested source snapshot")
    reviews = {}
    for name, role in (("specialist", "maize_evidence_specialist"),
                       ("verifier", "independent_verifier")):
        artifact = entry["review_artifacts"][name]
        path = _artifact(artifact["path"], artifact["sha256"], base_dir)
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("reviewer_role") != role:
            raise ValueError(f"{name} review has the wrong role")
        if report.get("reviewed_at") != entry["review_date"]:
            raise ValueError(f"{name} review date does not match the registry")
        if report.get("run_report_sha256") != frozen["sha256"]:
            raise ValueError(f"{name} review does not cite the frozen input hash")
        if Path(report.get("run_report", "")).name != input_path.name:
            raise ValueError(f"{name} review does not cite the frozen input")
        match = [item for item in report.get("reviews", [])
                 if item.get("review_id") == entry["review_id"]]
        if len(match) != 1 or match[0].get("text_sha256") != entry["text_sha256"]:
            raise ValueError(f"{name} review is not bound to the exact reviewed excerpt")
        if not match[0].get("sources") or any(
            item.get("url") not in expected_urls for item in match[0]["sources"]
        ):
            raise ValueError(f"{name} review cites a source outside the frozen case")
        reviews[name] = report
    comparison = compare_reviews(reviews["specialist"], reviews["verifier"])
    if comparison["status"] != "agent_agreement_official_sources":
        raise ValueError("the two AI reviews do not agree on supported official-source evidence")
    if any(item["review_id"] == entry["review_id"] for item in comparison["disagreements"]):
        raise ValueError("review case has a judgment disagreement")
    artifact = entry["comparison_artifact"]
    saved_path = _artifact(artifact["path"], artifact["sha256"], base_dir)
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    if saved.get("status") not in {"agent_agreement_official_sources", "contested_or_insufficient_evidence"}:
        raise ValueError("comparison artifact has an unknown status")
    if any(item.get("review_id") == entry["review_id"] for item in saved.get("disagreements", [])):
        raise ValueError("saved comparison records a disagreement for this case")
    if (saved.get("run_report_sha256") != frozen["sha256"]
            or saved.get("run_report") != reviews["specialist"].get("run_report")):
        raise ValueError("saved comparison does not cover the frozen review input")

    approval_artifact = entry["human_approval"]
    if not isinstance(approval_artifact, dict):
        raise ValueError("human_approval must identify a hashed approval artifact")
    approval_path = _artifact(approval_artifact["path"], approval_artifact["sha256"], base_dir)
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval_required = {
        "schema_version", "decision", "approver_type", "approver_id", "approver_role",
        "qualification_reference", "approved_at", "record_id", "review_id", "text_sha256",
        "source_id", "crop", "review_input_sha256", "source_snapshot_sha256", "content_sha256",
        "valid_from", "valid_until",
    }
    if not isinstance(approval, dict) or set(approval) != approval_required:
        raise ValueError("human approval artifact has an invalid schema")
    if (not isinstance(entry["approved_content_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", entry["approved_content_sha256"])
            or approval["content_sha256"] != entry["approved_content_sha256"]):
        raise ValueError("human approval must bind the exact canonical content and scope hash")
    if (approval["schema_version"] != 1 or approval["decision"] != "approve"
            or approval["approver_type"] != "human"
            or approval["approver_role"] != "qualified_agronomic_reviewer"):
        raise ValueError("explicit qualified human agronomic approval is required")
    for field in ("approver_id", "qualification_reference"):
        if not isinstance(approval[field], str) or not approval[field].strip():
            raise ValueError(f"human approval {field} is required")
    if approval["approver_id"].strip().casefold() in {
        "maize_evidence_specialist", "independent_verifier"
    }:
        raise ValueError("AI reviewer roles cannot approve knowledge")
    try:
        approved_at = date.fromisoformat(approval["approved_at"])
        review_date = date.fromisoformat(entry["review_date"])
    except (TypeError, ValueError) as exc:
        raise ValueError("human approval and review dates must use YYYY-MM-DD") from exc
    if approved_at < review_date or approval["approved_at"] != approved_at.isoformat():
        raise ValueError("human approval date must not precede source review")
    snapshot_path, snapshot_hash = snapshot_map[entry["source_id"]]
    expected_approval = {
        "record_id": entry["record_id"], "review_id": entry["review_id"],
        "text_sha256": entry["text_sha256"], "source_id": entry["source_id"],
        "crop": entry["crop"], "review_input_sha256": frozen["sha256"],
        "source_snapshot_sha256": snapshot_hash,
        "content_sha256": entry["approved_content_sha256"],
    }
    if any(approval.get(key) != value for key, value in expected_approval.items()):
        raise ValueError("human approval does not bind the exact reviewed source and excerpt")
    validity = {key: approval[key] for key in ("valid_from", "valid_until")}
    for key, value in validity.items():
        if value is not None:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError()
            except (TypeError, ValueError) as exc:
                raise ValueError(f"human approval {key} must be null or an ISO date") from exc
    if validity["valid_from"] and validity["valid_until"] and validity["valid_from"] > validity["valid_until"]:
        raise ValueError("human approval validity range is inverted")
    if (approval["approver_id"] != entry["approver_id"]
            or approval["approver_type"] != entry["approver_type"]):
        raise ValueError("human approval identity must match the registry entry")


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CurationRegistry:
    """Load exact excerpt approvals; malformed or absent registries allow nothing."""

    def __init__(self, path: str | Path | None = None, entries: dict | None = None,
                 base_dir: Path = PROJECT_ROOT):
        self.entries: dict[str, dict[str, Any]] = {}
        if entries is not None:
            self.entries = entries
            return
        if path is None:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION or not isinstance(payload.get("entries"), list):
                return
            for entry in payload["entries"]:
                if not isinstance(entry, dict) or not entry.get("record_id"):
                    raise ValueError("curation entry is invalid")
                record_id = str(entry["record_id"])
                if record_id in self.entries:
                    raise ValueError("duplicate curation record_id")
                validate_entry(entry, base_dir=base_dir)
                frozen_path = Path(entry["review_input"]["path"])
                frozen_path = frozen_path if frozen_path.is_absolute() else base_dir / frozen_path
                frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
                candidate = next(item for item in frozen.get("cases", [])
                                 if item.get("id") == entry["review_id"])
                entry["review_artifacts_verified"] = True
                entry["source_snapshots_verified"] = True
                entry["human_approval_verified"] = True
                entry["review_input_sha256"] = entry["review_input"]["sha256"]
                entry["_validated_scope"] = candidate["context"]
                approval_path = Path(entry["human_approval"]["path"])
                approval_path = approval_path if approval_path.is_absolute() else base_dir / approval_path
                approval = json.loads(approval_path.read_text(encoding="utf-8"))
                entry["_validated_validity"] = {
                    key: approval[key] for key in ("valid_from", "valid_until")
                }
                self.entries[record_id] = entry
        except (OSError, ValueError, TypeError, AttributeError, KeyError):
            self.entries = {}

    def authorizes(self, document: dict[str, Any]) -> bool:
        if not isinstance(document, dict):
            return False
        metadata = document.get("metadata", document)
        if not isinstance(metadata, dict):
            return False
        record_id = metadata.get("curation_record_id")
        entry = self.entries.get(str(record_id)) if record_id else None
        if not entry or entry.get("approval_status") != "approved":
            return False
        approved_scope = entry.get("_validated_scope", entry.get("approved_scope"))
        document_scope = metadata.get("approved_scope")
        if not isinstance(approved_scope, dict) or not approved_scope or document_scope != approved_scope:
            return False
        # The flat scope fields are consumed by retrieval filters. Bind them to the
        # exact object reviewed in the frozen candidate so edited metadata cannot widen scope.
        if any(metadata.get(key) != value for key, value in approved_scope.items()):
            return False
        non_scope_fields = {
            "curation_record_id", "knowledge_record_id", "knowledge_release_id",
            "source_id", "source", "knowledge_status", "review_status", "review_date",
            "reviewed_at", "review_input_sha256", "approved_scope", "valid_from", "valid_until",
            "text", "retrieval_distance",
        }
        flat_scope = {key: value for key, value in metadata.items()
                      if key not in non_scope_fields}
        if flat_scope != approved_scope:
            return False
        text = str(document.get("text", "")).strip()
        source = metadata.get("source_id") or metadata.get("source")
        crop = str(metadata.get("crop", "")).strip().casefold()
        review_date = metadata.get("review_date") or metadata.get("reviewed_at")
        validity_ok = True
        valid_from = metadata.get("valid_from")
        valid_until = metadata.get("valid_until")
        approved_validity = entry.get("_validated_validity", {
            "valid_from": entry.get("approved_valid_from"),
            "valid_until": entry.get("approved_valid_until"),
        })
        if (valid_from != approved_validity.get("valid_from")
                or valid_until != approved_validity.get("valid_until")):
            return False
        try:
            if valid_from is not None:
                validity_ok = validity_ok and date.fromisoformat(valid_from) <= date.today()
            if valid_until is not None:
                validity_ok = validity_ok and date.today() <= date.fromisoformat(valid_until)
        except (TypeError, ValueError):
            validity_ok = False
        return bool(
            text
            and validity_ok
            and entry.get("text_sha256") == text_sha256(text)
            and entry.get("source_id") == source
            and str(entry.get("crop", "")).casefold() == crop
            and entry.get("review_date") == review_date
            and entry.get("review_artifacts_verified") is True
            and entry.get("source_snapshots_verified") is True
            and entry.get("human_approval_verified") is True
            and entry.get("review_input_sha256")
        )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Validate runtime curation approvals and linked AI reviews.")
    parser.add_argument("registry", nargs="?", default=str(PROJECT_ROOT / "data" / "curation_registry.json"))
    args = parser.parse_args()
    path = Path(args.registry).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION or not isinstance(payload.get("entries"), list):
            raise ValueError("unsupported registry schema")
        ids = set()
        for entry in payload["entries"]:
            if entry.get("record_id") in ids:
                raise ValueError("duplicate record_id")
            ids.add(entry.get("record_id"))
            validate_entry(entry, base_dir=PROJECT_ROOT)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"CURATION REGISTRY: INVALID ({exc})")
        return 1
    print(f"CURATION REGISTRY: VALID ({len(ids)} approved excerpts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
