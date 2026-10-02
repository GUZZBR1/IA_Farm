"""Human-review packages and fail-closed publication prerequisites.

This module stores a review decision shape; it cannot authenticate the person
behind reviewer_id. Authentication, qualification checks, and durable audit
append must be provided by the operating environment.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from tools.source_snapshots import (
    LICENSE_STATUSES, validate_license_status, validate_locator, verify_snapshot,
)

DECISIONS = frozenset({
    "APPROVE", "REJECT", "NEEDS_CHANGES", "INSUFFICIENT_EVIDENCE",
    "CONFLICT_REQUIRES_RESOLUTION",
})
RISK_REVIEW_POLICY = {
    "LOW": {"qualified_reviewers": 1, "independent_verification": False},
    "MEDIUM": {"qualified_reviewers": 1, "independent_verification": True},
    "HIGH": {"qualified_reviewers": 2, "independent_verification": True},
    "CRITICAL": {"qualified_reviewers": None, "independent_verification": None},
}
ALLOWED_PUBLICATION_LICENSES = frozenset({
    "REDISTRIBUTION_ALLOWED", "ATTRIBUTION_REQUIRED", "PUBLIC_DOMAIN",
})


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_human_review(review: Any, *, candidate_hash: str,
                          snapshot_hash: str, scope: dict[str, Any]) -> None:
    if not isinstance(review, dict):
        raise ValueError("an explicit human review is required")
    required = {
        "reviewer_id", "reviewer_role", "qualification", "reviewed_at", "decision",
        "scope", "comments", "source_snapshot_hash", "candidate_content_hash", "limitations",
    }
    if set(review) != required:
        raise ValueError("human review has missing or unexpected fields")
    for key in ("reviewer_id", "reviewer_role", "qualification", "comments"):
        if not isinstance(review[key], str) or not review[key].strip():
            raise ValueError(f"human review {key} must be non-empty")
    try:
        date.fromisoformat(review["reviewed_at"])
    except (TypeError, ValueError) as exc:
        raise ValueError("reviewed_at must be an ISO calendar date") from exc
    if not isinstance(review["decision"], str) or review["decision"] not in DECISIONS:
        raise ValueError("unknown human review decision")
    if review["candidate_content_hash"] != candidate_hash:
        raise ValueError("review applies to different candidate content; approval is invalidated")
    if review["source_snapshot_hash"] != snapshot_hash:
        raise ValueError("review applies to a different source snapshot")
    if review["scope"] != scope:
        raise ValueError("review applies to a different scope")
    if not isinstance(review["limitations"], list) or any(not isinstance(x, str) for x in review["limitations"]):
        raise ValueError("limitations must be a list of strings")


def build_review_package(candidate: dict[str, Any], *, snapshot: dict[str, Any] | None,
                         locator: dict[str, Any] | None, exact_evidence: str | None,
                         evidence_text: str, evidence_page: int | str,
                         evidence_extraction_method: str, storage_root: Path,
                         conflicting_evidence: list[dict[str, Any]] | None = None,
                         ai_reviewer_notes: list[str] | None = None,
                         proposed_decision: str = "INSUFFICIENT_EVIDENCE") -> dict[str, Any]:
    """Prepare a reviewer-facing packet; AI notes remain explicitly untrusted."""
    if proposed_decision not in DECISIONS:
        raise ValueError("proposed_decision is not an allowed review outcome")
    if (not isinstance(snapshot, dict)
            or not re.fullmatch(r"[0-9a-f]{64}", str(snapshot.get("content_hash", "")))):
        raise ValueError("a verified source snapshot is required before preparing a review package")
    if not verify_snapshot(snapshot, storage_root=storage_root):
        raise ValueError("source snapshot bytes do not match the declared hash and size")
    if snapshot.get("snapshot_id") != f"{snapshot.get('source_id')}:{snapshot.get('content_hash')}":
        raise ValueError("snapshot identity does not bind the source ID and content hash")
    if not exact_evidence or not exact_evidence.strip():
        raise ValueError("exact evidence from the frozen snapshot is required")
    if not isinstance(evidence_text, str) or exact_evidence not in evidence_text:
        raise ValueError("exact evidence is not present in the supplied extracted snapshot text")
    if not isinstance(evidence_extraction_method, str) or not evidence_extraction_method.strip():
        raise ValueError("evidence extraction method is required")
    if locator is not None:
        validate_locator(locator, snapshot_id=snapshot.get("snapshot_id"),
                         snapshot_hash=snapshot.get("content_hash"))
    else:
        raise ValueError("a snapshot-relative evidence locator is required")
    evidence_hash = hashlib.sha256(exact_evidence.encode("utf-8")).hexdigest()
    if locator.get("quote_hash") != evidence_hash:
        raise ValueError("locator quote_hash does not match the exact evidence text")
    locator_page = locator.get("page", locator.get("page_start"))
    if isinstance(locator_page, int) and evidence_page != locator_page:
        raise ValueError("extracted evidence page does not match the locator page")
    content_hash = canonical_hash({k: candidate[k] for k in sorted(candidate) if k not in {"review_status"}})
    return {
        "schema_version": 1, "candidate_id": candidate.get("candidate_id"),
        "claim": candidate.get("claim"), "context": candidate.get("context", {}),
        "crop": candidate.get("crop"), "region": candidate.get("region"),
        "conditions": candidate.get("conditions", {}),
        "source_metadata": snapshot,
        "snapshot_hash": snapshot.get("content_hash") if snapshot else None,
        "candidate_content_hash": content_hash, "locator": locator,
        "exact_evidence": exact_evidence,
        "evidence_extraction": {
            "method": evidence_extraction_method,
            "page_or_fragment": evidence_page,
            "extracted_text_sha256": hashlib.sha256(evidence_text.encode("utf-8")).hexdigest(),
            "source_snapshot_hash": snapshot.get("content_hash"),
            "manual_locator_verification_required": True,
        },
        "conflicting_evidence": conflicting_evidence or [],
        "ai_reviewer_notes": [{"origin": "AI", "not_human_review": True, "note": note}
                              for note in (ai_reviewer_notes or [])],
        "risk_classification": candidate.get("risk_level", "UNASSESSED"),
        "questions_for_reviewer": list(candidate.get("review_questions", [])),
        "proposed_decision": proposed_decision,
        "decision_is_suggestion_only": True,
    }


def promotion_blockers(*, snapshot: dict[str, Any] | None,
                       snapshot_valid: bool, locator: dict[str, Any] | None,
                       license_status: str | None, schema_valid: bool,
                       scope: dict[str, Any] | None, human_review: dict[str, Any] | None,
                       candidate_hash: str, conflict_blocking: bool,
                       deprecated: bool, license_evidence_ref: str | None = None,
                       license_evidence_valid: bool = False,
                       license_attribution: str | None = None,
                       valid_until: str | None = None,
                       today: date | None = None) -> list[str]:
    """Return every reason a record cannot be published; empty means structural gates pass."""
    blockers: list[str] = []
    if (not snapshot or not re.fullmatch(r"[0-9a-f]{64}",
                                         str(snapshot.get("content_hash", "")))):
        blockers.append("SOURCE_SNAPSHOT_MISSING")
    elif not snapshot_valid:
        blockers.append("SOURCE_SNAPSHOT_INVALID_OR_CHANGED")
    if not locator:
        blockers.append("EVIDENCE_LOCATOR_MISSING")
    else:
        try:
            validate_locator(
                locator,
                snapshot_id=snapshot.get("snapshot_id") if snapshot else None,
                snapshot_hash=snapshot.get("content_hash") if snapshot else None,
            )
        except ValueError:
            blockers.append("EVIDENCE_LOCATOR_INVALID")
    try:
        validate_license_status(license_status)
    except ValueError:
        blockers.append("LICENSE_DECISION_MISSING")
    else:
        if license_status not in ALLOWED_PUBLICATION_LICENSES:
            blockers.append("LICENSE_POLICY_BLOCKS_PUBLICATION")
        if not isinstance(license_evidence_ref, str) or not license_evidence_ref.strip():
            blockers.append("LICENSE_EVIDENCE_MISSING")
        elif not license_evidence_valid:
            blockers.append("LICENSE_EVIDENCE_INVALID")
        if license_status == "ATTRIBUTION_REQUIRED" and not license_attribution:
            blockers.append("LICENSE_ATTRIBUTION_MISSING")
    if not schema_valid:
        blockers.append("KNOWLEDGE_SCHEMA_INVALID")
    if (not isinstance(scope, dict) or not scope
            or any(v is None or isinstance(v, str) and not v.strip() for v in scope.values())):
        blockers.append("SCOPE_MISSING_OR_INCOMPLETE")
    if not re.fullmatch(r"[0-9a-f]{64}", str(candidate_hash)):
        blockers.append("CANDIDATE_CONTENT_HASH_INVALID")
    if human_review is None:
        blockers.append("HUMAN_REVIEW_MISSING")
    elif not snapshot:
        blockers.append("HUMAN_REVIEW_CANNOT_BIND_MISSING_SNAPSHOT")
    else:
        try:
            validate_human_review(human_review, candidate_hash=candidate_hash,
                                  snapshot_hash=snapshot["content_hash"], scope=scope or {})
        except (ValueError, KeyError, TypeError):
            blockers.append("HUMAN_REVIEW_HASH_OR_SCOPE_MISMATCH")
        else:
            if human_review.get("decision") != "APPROVE":
                blockers.append("HUMAN_REVIEW_NOT_APPROVED")
    if conflict_blocking:
        blockers.append("UNRESOLVED_EVIDENCE_CONFLICT")
    if deprecated:
        blockers.append("KNOWLEDGE_DEPRECATED")
    if valid_until:
        try:
            if (today or date.today()) > date.fromisoformat(valid_until):
                blockers.append("KNOWLEDGE_EXPIRED")
        except ValueError:
            blockers.append("VALIDITY_DATE_INVALID")
    return blockers


def validate_conflict(conflict: Any) -> None:
    required = {
        "conflict_id", "candidate_id", "source_a", "source_b", "difference_type",
        "scope_difference", "publication_date_difference", "regional_difference",
        "methodological_difference", "unresolved_question", "resolution_status",
    }
    if not isinstance(conflict, dict) or set(conflict) != required:
        raise ValueError("conflict record schema is invalid")
    if conflict["source_a"] == conflict["source_b"]:
        # A single-source reviewer disagreement is represented as provenance differences,
        # not falsely described as a conflict between documents.
        if conflict["difference_type"] != "AI_REVIEW_DISAGREEMENT":
            raise ValueError("same-source reviewer disagreement must be identified as such")
    if conflict["resolution_status"] != "UNRESOLVED":
        raise ValueError("conflicts remain blocked until an explicit resolution artifact exists")
