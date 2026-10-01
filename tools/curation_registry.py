"""Fail-closed runtime allowlist for exact, reviewed source excerpts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _artifact(path_value: str, expected_sha256: str, base_dir: Path) -> Path:
    path = Path(path_value)
    path = path if path.is_absolute() else base_dir / path
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError(f"curation artifact missing or hash mismatch: {path_value}")
    return path


def validate_entry(entry: dict[str, Any], base_dir: Path = PROJECT_ROOT) -> None:
    """Verify the frozen input, two source reviews, and same-case agreement."""
    required = (
        "record_id", "review_id", "text_sha256", "source_id", "crop",
        "review_date", "review_input", "review_artifacts", "comparison_artifact",
    )
    if any(not entry.get(field) for field in required):
        raise ValueError("curation entry is missing required provenance fields")
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
    known_sources = {
        item.get("id"): item.get("url")
        for item in candidate_set.get("sources", []) if isinstance(item, dict)
    }
    expected_urls = {known_sources.get(source_id) for source_id in candidate["source_ids"]}
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
    sys.path.insert(0, str(PROJECT_ROOT / "tests"))
    from verify_agronomist_reviews import compare_reviews
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
            if payload.get("schema_version") != 1 or not isinstance(payload.get("entries"), list):
                return
            for entry in payload["entries"]:
                if not isinstance(entry, dict) or not entry.get("record_id"):
                    return
                record_id = str(entry["record_id"])
                if record_id in self.entries:
                    return
                validate_entry(entry, base_dir=base_dir)
                entry["review_artifacts_verified"] = True
                entry["review_input_sha256"] = entry["review_input"]["sha256"]
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
        text = str(document.get("text", "")).strip()
        source = metadata.get("source_id") or metadata.get("source")
        crop = str(metadata.get("crop", "")).strip().casefold()
        review_date = metadata.get("review_date") or metadata.get("reviewed_at")
        return bool(
            text
            and entry.get("text_sha256") == text_sha256(text)
            and entry.get("source_id") == source
            and str(entry.get("crop", "")).casefold() == crop
            and entry.get("review_date") == review_date
            and entry.get("review_artifacts_verified") is True
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
        if payload.get("schema_version") != 1 or not isinstance(payload.get("entries"), list):
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
