"""Build the operational source-acquisition queue from frozen audit inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.human_review import validate_conflict

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "tests" / "agronomic_gold_candidates.json"
DEFAULT_AUDIT = ROOT / "tests" / "agronomic_candidate_audit.json"
DEFAULT_CONFLICTS = ROOT / "tests" / "agronomic_candidate_conflicts.json"
DEFAULT_OUTPUT = ROOT / "tests" / "agronomic_candidate_queue.json"

NEXT_ACTIONS = {
    "DRAFT-MZ-SOIL-001": "Capture the cited PDF, map the exact claim span, and verify present applicability.",
    "DRAFT-MZ-SOIL-002": "Capture the PDF and ask a qualified reviewer to resolve the scope/qualification disagreement.",
    "DRAFT-MZ-ZARC-001": "Capture the named current ordinance/manual versions and reconcile the broad page with exact references.",
    "DRAFT-MZ-ZARC-002": "Acquire the exact current ordinance and annex covering municipality and season; the listing page is insufficient.",
    "DRAFT-MZ-FERT-001": "Capture the current page, establish version/date, and review the evidence supporting abstention.",
    "DRAFT-MZ-IRR-001": "Capture the cited artifact and reconcile the PDF reference with the separately cited HTML material.",
    "DRAFT-MZ-IRR-002": "Capture exact sources and preserve the no-calculation boundary while required inputs are absent.",
    "DRAFT-MZ-PEST-001": "Register and capture the exact FAQ/cartilha cited by each reviewer, then reconcile source identity.",
    "DRAFT-MZ-PEST-002": "Capture each cited document and have a qualified reviewer assess inference and diagnostic scope.",
    "DRAFT-MZ-PEST-006": "Capture the exact cited cartilha; repository landing metadata alone does not locate claim evidence.",
    "DRAFT-MZ-PEST-003": "Capture the diagnostic pages and determine what evidence a photo can and cannot support.",
    "DRAFT-MZ-PEST-004": "Capture the cited source; no pesticide/product registration or dose evidence is currently identified.",
    "DRAFT-MZ-PEST-005": "Resolve the integrated-braquiaria source scope against the candidate's declared monoculture context.",
    "DRAFT-MZ-PHENOLOGY-001": "Capture the PDF and locate each requested stage label and mapping for review.",
    "DRAFT-MZ-WATER-003": "Capture the PDF and separately cited HTML source; establish source identity and exact claim scope.",
    "DRAFT-MZ-HARVEST-001": "Capture the PDF and review whether the historical passage supports the candidate's exact scope.",
    "DRAFT-MZ-HARVEST-002": "Capture and locate the relevant harvest/weather passages; forecast context is currently absent.",
    "DRAFT-MZ-STORAGE-001": "Reconcile the two cited postharvest editions and resolve answer-versus-abstention evidence.",
}


def build_queue(candidates: dict[str, Any], audit: dict[str, Any],
                conflict_data: dict[str, Any] | None = None) -> dict[str, Any]:
    source_by_id = {item["id"]: item for item in candidates["sources"]}
    audit_by_id = {item["case_id"]: item for item in audit["cases"]}
    if conflict_data is None and DEFAULT_CONFLICTS.is_file():
        conflict_data = json.loads(DEFAULT_CONFLICTS.read_text(encoding="utf-8"))
    conflicts_by_id = {}
    for item in (conflict_data or {}).get("conflicts", []):
        validate_conflict(item)
        conflicts_by_id.setdefault(item["candidate_id"], []).append(item)
    rows = []
    for case in candidates["cases"]:
        case_id = case["id"]
        result = audit_by_id[case_id]
        sources = []
        for source_id in case["source_ids"]:
            src = source_by_id[source_id]
            sources.append({
                "source_id": source_id, "institution": src.get("publisher"),
                "url": src.get("url"), "document_title": src.get("title"),
                "document_version": src.get("version") or src.get("edition"),
                "publication_date": src.get("published_at"),
                "updated_at": src.get("updated_at"),
                "locator_hint_unverified": src.get("evidence_locations"),
                # A license note is not a complete license decision or rights evidence.
                "license_status": "UNKNOWN",
                "license_note_unverified": src.get("license_note"),
                "snapshot_present": False,
            })
        primary = ("EVIDENCE_CONFLICT" if result["classification"] == "CONFLICTING_EVIDENCE"
                   else "SNAPSHOT_MISSING")
        rows.append({
            "candidate_id": case_id,
            "topic": case_id.removeprefix("DRAFT-MZ-").rsplit("-", 1)[0],
            "claim_question": case["question"],
            "current_status": result.get("candidate_status", "pending_agronomist_review"),
            "queue": primary,
            "required_sources": case["source_ids"],
            "required_source": case["source_ids"],
            "known_source": sources,
            "known_sources": sources,
            "source_institution": [src["institution"] for src in sources],
            "source_url": [src["url"] for src in sources],
            "document_title": [src["document_title"] for src in sources],
            "document_version": [src["document_version"] for src in sources],
            "publication_date": [src["publication_date"] for src in sources],
            "required_locator": [src["locator_hint_unverified"] for src in sources],
            "known_locator": [src["locator_hint_unverified"] for src in sources],
            "license_status": "UNKNOWN",
            "context": case.get("context", {}),
            "source_snapshot_status": "MISSING",
            "locator_status": "UNVERIFIED_NARRATIVE_HINT_ONLY",
            "evidence_status": result["classification"],
            "review_blockers": [
                "SOURCE_SNAPSHOT_MISSING", "EXACT_EVIDENCE_NOT_HASHED",
                "LOCATOR_NOT_VERIFIED_AGAINST_SNAPSHOT", "LICENSE_UNKNOWN",
                "QUALIFIED_HUMAN_APPROVAL_MISSING",
            ] + (["AI_REVIEW_DISAGREEMENT_UNRESOLVED"] if primary == "EVIDENCE_CONFLICT" else []),
            "conflict_summary": (result["rationale"] if primary == "EVIDENCE_CONFLICT" else None),
            "conflicts": conflicts_by_id.get(case_id, []),
            "next_action": NEXT_ACTIONS[case_id],
            "approved": False,
        })
    return {
        "schema_version": 1,
        "queue_status": "OPERATIONAL_TRIAGE_NOT_AGRONOMIC_VALIDATION",
        "source_references_are_not_ingested_sources": True,
        "reviewer_disagreement_is_not_source_conflict_proof": True,
        "source_set_version": candidates["candidate_set_version"],
        "counts": {
            "total": len(rows),
            "SOURCE_MISSING": sum(row["queue"] == "SOURCE_MISSING" for row in rows),
            "SNAPSHOT_MISSING": sum(row["queue"] == "SNAPSHOT_MISSING" for row in rows),
            "LOCATOR_MISSING": sum(row["queue"] == "LOCATOR_MISSING" for row in rows),
            "LICENSE_UNKNOWN": sum(any(src["license_status"] == "UNKNOWN" for src in row["known_sources"]) for row in rows),
            "EVIDENCE_INSUFFICIENT": sum(row["evidence_status"] == "INSUFFICIENT_EVIDENCE" for row in rows),
            "EVIDENCE_CONFLICT": sum(row["queue"] == "EVIDENCE_CONFLICT" for row in rows),
            "READY_FOR_HUMAN_REVIEW": 0,
            "OUT_OF_SCOPE": 0,
        },
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    result = build_queue(candidates, audit)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
