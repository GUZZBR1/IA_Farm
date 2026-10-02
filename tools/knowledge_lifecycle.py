"""Explicit knowledge transitions and append-only audit events, without indexing.

Callers must persist each returned record and event atomically, append events
without rewriting/deleting prior events, and compare the prior audit_head before
committing to prevent lost updates. A vector index is a disposable projection,
never the authoritative knowledge store. Actor types are auditable assertions,
not cryptographic identity proof; callers authenticate and authorize operators.
Deprecation time is the DEPRECATED event's `at` timestamp, retained in the audit
chain. Context dimensions (region, soil, stage, climate, applicability, etc.) are
optional keys in `scope`; approval requires its provided keys in the frozen case.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from tools.curation_registry import PROJECT_ROOT, validate_entry
from tools.knowledge_schema import (
    SCHEMA_VERSION, AuditEvent, KnowledgeRecord, KnowledgeStatus,
    content_sha256, json_sha256, record_sha256, timestamp,
    validate_audit_event, validate_record,
)

ALLOWED_TRANSITIONS = {
    "RAW": frozenset({"PARSED", "REJECTED"}),
    "PARSED": frozenset({"CANDIDATE", "REJECTED"}),
    "CANDIDATE": frozenset({"UNDER_REVIEW", "REJECTED"}),
    "UNDER_REVIEW": frozenset({"APPROVED", "REJECTED", "CANDIDATE"}),
    "APPROVED": frozenset({"PUBLISHED", "DEPRECATED", "UNDER_REVIEW"}),
    "REJECTED": frozenset({"CANDIDATE"}),
    "DEPRECATED": frozenset({"UNDER_REVIEW"}),
    "PUBLISHED": frozenset({"DEPRECATED"}),
}


def _actor(actor_id: str, actor_type: str, reason: str) -> None:
    if not isinstance(actor_id, str) or not actor_id.strip():
        raise ValueError("actor_id must be a non-empty string")
    if not isinstance(actor_type, str) or actor_type not in {"human", "agent", "system"}:
        raise ValueError("actor_type must be human, agent, or system")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("every transition requires an explicit reason")


def _event(before: KnowledgeRecord | None, after: KnowledgeRecord, *,
           actor_id: str, actor_type: str, reason: str, at: str) -> AuditEvent:
    event: AuditEvent = {
        "schema_version": SCHEMA_VERSION, "event_id": str(uuid4()),
        "record_id": after["record_id"], "revision": after["revision"],
        "from_status": before["status"] if before else None,
        "to_status": after["status"], "actor_id": actor_id,
        "actor_type": actor_type, "reason": reason, "at": at,
        "before_sha256": record_sha256(before) if before else None,
        "after_sha256": record_sha256(after),
        "previous_event_sha256": before["audit_head"] if before else None,
        "event_sha256": "",
    }
    event["event_sha256"] = json_sha256({
        key: value for key, value in event.items() if key != "event_sha256"
    })
    after["audit_head"] = event["event_sha256"]
    validate_record(after)
    validate_audit_event(event)
    return event


def new_record(record_id: str, text: str, sources: list[dict[str, Any]],
               scope: dict[str, Any], *, actor_id: str, at: str,
               actor_type: str = "agent", content_type: str | None = None,
               supersedes: str | None = None) -> tuple[KnowledgeRecord, AuditEvent]:
    """Create RAW knowledge only. Imported approval fields are never accepted."""
    _actor(actor_id, actor_type, "create raw record")
    timestamp(at)
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    record: KnowledgeRecord = {
        "schema_version": SCHEMA_VERSION, "record_id": record_id,
        "revision": 1, "status": "RAW", "text": text,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "sources": copy.deepcopy(sources), "scope": copy.deepcopy(scope),
        "created_at": at, "updated_at": at, "created_by": actor_id,
        "approval": None, "audit_head": "0" * 64,
    }
    if content_type is not None:
        record["content_type"] = content_type
    if supersedes is not None:
        record["supersedes"] = supersedes
    event = _event(None, record, actor_id=actor_id, actor_type=actor_type,
                   reason="create raw record", at=at)
    return record, event


def _verified_approval(record: KnowledgeRecord, review_entry: Any, *,
                       actor_id: str, actor_type: str, at: str,
                       base_dir: Path) -> dict[str, Any]:
    if actor_type != "human":
        raise ValueError("approval/publication requires an explicit human action")
    if not isinstance(review_entry, dict) or review_entry.get("approval_status") != "approved":
        raise ValueError("an external approved curation entry is required")
    if not isinstance(review_entry.get("human_approval"), dict):
        raise ValueError("a separate explicit human approval artifact is required")
    reviewer_ids = review_entry.get("reviewer_ids")
    approver = review_entry.get("approver_id")
    if (not isinstance(reviewer_ids, list) or len(reviewer_ids) != 2
            or any(not isinstance(value, str) or not value.strip() for value in reviewer_ids)
            or not isinstance(approver, str) or not approver.strip()
            or actor_id != approver or review_entry.get("approver_type") != "human"):
        raise ValueError("a distinct explicit human approver must perform this transition")
    reviewers = {value.strip().casefold() for value in reviewer_ids}
    if (reviewers != {"maize_evidence_specialist", "independent_verifier"}
            or approver.strip().casefold() in reviewers):
        raise ValueError("reviewer_ids must identify two distinct reviewers separate from the approver")
    if (review_entry.get("record_id") != record["record_id"]
            or review_entry.get("text_sha256") != record["text_sha256"]
            or review_entry.get("crop") != record["scope"].get("crop")):
        raise ValueError("external review does not cover this record's identity/text/crop")
    if review_entry.get("approved_content_sha256") != content_sha256(record):
        raise ValueError("human sign-off does not bind the exact canonical content and scope")
    snapshots = review_entry.get("source_snapshots")
    if (not isinstance(snapshots, list) or not snapshots
            or any(not isinstance(snapshot, dict) for snapshot in snapshots)):
        raise ValueError("external review requires bound source_snapshots")
    for source in record["sources"]:
        from tools.human_review import ALLOWED_PUBLICATION_LICENSES
        from tools.source_snapshots import validate_locator
        if source.get("license_status") not in ALLOWED_PUBLICATION_LICENSES:
            raise ValueError("a compatible explicit license decision is required")
        if not source.get("license_evidence_ref") or not source.get("license_evidence_sha256"):
            raise ValueError("verified license evidence is required")
        if source.get("license_status") == "ATTRIBUTION_REQUIRED" and not source.get("license_attribution"):
            raise ValueError("license-required attribution is missing")
        validate_locator(source.get("evidence_locator"),
                         snapshot_id=f"{source['source_id']}:{source['snapshot_sha256']}",
                         snapshot_hash=source["snapshot_sha256"])
        if not source.get("snapshot_ref") or not source.get("snapshot_sha256"):
            raise ValueError("source URL references alone do not prove source ingestion")
        matches = [snapshot for snapshot in snapshots if snapshot.get("source_id") == source["source_id"]]
        if (len(matches) != 1 or matches[0].get("path") != source["snapshot_ref"]
                or matches[0].get("sha256") != source["snapshot_sha256"]):
            raise ValueError("external review does not bind this exact source snapshot")
        snapshot = Path(source["snapshot_ref"])
        snapshot = snapshot if snapshot.is_absolute() else base_dir / snapshot
        try:
            if (not snapshot.is_file()
                    or hashlib.sha256(snapshot.read_bytes()).hexdigest() != source["snapshot_sha256"]):
                raise ValueError("source snapshot is missing or its SHA-256 does not match")
        except OSError as error:
            raise ValueError("source snapshot cannot be read") from error
        license_path = Path(source["license_evidence_ref"])
        license_path = license_path if license_path.is_absolute() else base_dir / license_path
        try:
            license_path = license_path.resolve()
            if Path(base_dir).resolve() not in license_path.parents:
                raise ValueError("license evidence path escapes the approved artifact root")
            if (not license_path.is_file()
                    or hashlib.sha256(license_path.read_bytes()).hexdigest() != source["license_evidence_sha256"]):
                raise ValueError("license evidence is missing or its SHA-256 does not match")
        except OSError as error:
            raise ValueError("license evidence cannot be read") from error
    # Agreement is supporting evidence, never the approval decision itself.
    # This checks the actual frozen input and independently hashed artifacts.
    try:
        validate_entry(review_entry, base_dir=base_dir)
        human_path = Path(review_entry["human_approval"]["path"])
        human_path = human_path if human_path.is_absolute() else base_dir / human_path
        human_approval = json.loads(human_path.read_text(encoding="utf-8"))
        if (human_approval.get("approver_id") != actor_id
                or human_approval.get("approver_type") != "human"
                or human_approval.get("content_sha256") != content_sha256(record)
                or date.fromisoformat(human_approval["approved_at"]) > timestamp(at).date()):
            raise ValueError("transition actor/date does not match the explicit human approval")
        input_path = Path(review_entry["review_input"]["path"])
        input_path = input_path if input_path.is_absolute() else base_dir / input_path
        frozen = json.loads(input_path.read_text(encoding="utf-8"))
        candidate = next(item for item in frozen["cases"]
                         if item.get("id") == review_entry["review_id"])
        frozen_sources = {item["id"]: item["url"] for item in frozen["sources"]}
        if (review_entry["source_id"] not in {item["source_id"] for item in record["sources"]}
                or any(source["source_id"] not in candidate["source_ids"]
                       or source["url"] != frozen_sources.get(source["source_id"])
                       for source in record["sources"])
                 or candidate.get("context") != record["scope"]):
            raise ValueError("external review does not cover all source URLs and scope fields")
    except (OSError, KeyError, TypeError, AttributeError, StopIteration) as error:
        raise ValueError("external review artifacts are missing or malformed") from error
    return {
        "review_id": review_entry["review_id"], "reviewer_ids": copy.deepcopy(reviewer_ids),
        "approver_id": approver, "approver_type": "human",
        "reviewed_at": review_entry["review_date"], "approved_at": at,
        "content_sha256": content_sha256(record),
        "review_entry_sha256": json_sha256(review_entry),
    }


def transition_record(record: KnowledgeRecord, target_status: KnowledgeStatus, *,
                      actor_id: str, reason: str, at: str,
                      actor_type: str = "agent", review_entry: dict[str, Any] | None = None,
                      base_dir: Path = PROJECT_ROOT) -> tuple[KnowledgeRecord, AuditEvent]:
    """Return a new revision and audit event; never mutate caller-owned inputs.

    APPROVED and PUBLISHED both require a validated external curation entry and
    an explicit human approver distinct from the reviewer. PUBLISHED rechecks
    artifact hashes and the exact approval entry; record flags grant no authority.
    """
    validate_record(record)
    _actor(actor_id, actor_type, reason)
    if not isinstance(target_status, str) or target_status not in ALLOWED_TRANSITIONS[record["status"]]:
        raise ValueError(f"transition {record['status']} -> {target_status} is not allowed")
    if timestamp(at) < timestamp(record["updated_at"], "updated_at"):
        raise ValueError("transition timestamp cannot precede the current revision")
    result = copy.deepcopy(record)
    if target_status in {"APPROVED", "PUBLISHED"}:
        approval = _verified_approval(record, copy.deepcopy(review_entry), actor_id=actor_id,
                                      actor_type=actor_type, at=at, base_dir=Path(base_dir))
        if target_status == "APPROVED":
            result["approval"] = approval
        elif (record["approval"] is None
              or any(record["approval"][key] != approval[key]
                     for key in approval if key != "approved_at")):
            raise ValueError("publication requires the same explicit approval and reviewed content")
    elif target_status != "DEPRECATED":
        result["approval"] = None
    result["status"] = target_status
    result["revision"] += 1
    result["updated_at"] = at
    event = _event(record, result, actor_id=actor_id, actor_type=actor_type, reason=reason, at=at)
    return result, event


def validate_audit_chain(events: Iterable[AuditEvent],
                         record: KnowledgeRecord | None = None) -> None:
    """Validate a complete per-record chain, optionally binding its latest record.

    A chain detects alteration and reordering given a trusted stored head. It
    does not replace caller authentication or an append-only persistence layer.
    """
    previous = None
    count = 0
    for event in events:
        validate_audit_event(event)
        if previous is None:
            if (event["revision"] != 1 or event["from_status"] is not None
                    or event["to_status"] != "RAW" or event["before_sha256"] is not None
                    or event["previous_event_sha256"] is not None):
                raise ValueError("audit chain must start with RAW creation")
        elif (event["record_id"] != previous["record_id"]
              or event["revision"] != previous["revision"] + 1
              or event["previous_event_sha256"] != previous["event_sha256"]
              or event["before_sha256"] != previous["after_sha256"]
              or event["from_status"] != previous["to_status"]
              or event["to_status"] not in ALLOWED_TRANSITIONS[event["from_status"]]
              or timestamp(event["at"]) < timestamp(previous["at"])):
            raise ValueError("audit chain is altered, reordered, or incomplete")
        if event["to_status"] in {"APPROVED", "PUBLISHED"} and event["actor_type"] != "human":
            raise ValueError("audit approval/publication must be an explicit human action")
        previous = event
        count += 1
    if count == 0:
        raise ValueError("audit chain cannot be empty")
    if record is not None:
        validate_record(record)
        if (record["record_id"] != previous["record_id"]
                or record["revision"] != previous["revision"]
                or record["status"] != previous["to_status"]
                or record["updated_at"] != previous["at"]
                or record["audit_head"] != previous["event_sha256"]
                or record_sha256(record) != previous["after_sha256"]):
            raise ValueError("record does not match the latest audit event")
