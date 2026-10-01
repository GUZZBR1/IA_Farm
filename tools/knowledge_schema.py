"""Versioned JSON contracts for knowledge records, separate from vector indexes.

Validation checks structure and content binding. It does not authenticate a human
identity or grant approval: only the lifecycle API validates external review
artifacts before approving or publishing a record.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any, Literal, TypedDict
from urllib.parse import urlsplit

SCHEMA_VERSION = 1
KnowledgeStatus = Literal[
    "RAW", "PARSED", "CANDIDATE", "UNDER_REVIEW", "APPROVED", "REJECTED",
    "DEPRECATED", "PUBLISHED",
]
STATUSES = frozenset(KnowledgeStatus.__args__)


class SourceMetadata(TypedDict, total=False):
    edition: str
    version: str
    publication_date: str
    page: str | int
    section: str
    license: str
    valid_from: str
    valid_until: str
    snapshot_ref: str
    snapshot_sha256: str
    license_status: str
    license_attribution: str
    license_evidence_ref: str
    license_evidence_sha256: str
    evidence_locator: dict[str, Any]


class SourceReference(SourceMetadata):
    source_id: str
    url: str
    title: str
    publisher: str
    locator: str
    accessed_at: str


class Approval(TypedDict):
    review_id: str
    reviewer_ids: list[str]
    approver_id: str
    approver_type: Literal["human"]
    reviewed_at: str
    approved_at: str
    content_sha256: str
    review_entry_sha256: str


class KnowledgeMetadata(TypedDict, total=False):
    content_type: str
    supersedes: str


class KnowledgeRecord(KnowledgeMetadata):
    schema_version: int
    record_id: str
    revision: int
    status: KnowledgeStatus
    text: str
    text_sha256: str
    sources: list[SourceReference]
    scope: dict[str, Any]
    created_at: str
    updated_at: str
    created_by: str
    approval: Approval | None
    audit_head: str


class AuditEvent(TypedDict):
    schema_version: int
    event_id: str
    record_id: str
    revision: int
    from_status: KnowledgeStatus | None
    to_status: KnowledgeStatus
    actor_id: str
    actor_type: Literal["human", "agent", "system"]
    reason: str
    at: str
    before_sha256: str | None
    after_sha256: str
    previous_event_sha256: str | None
    event_sha256: str


def json_sha256(value: Any) -> str:
    """Hash canonical JSON; reject non-JSON objects and non-finite numbers."""
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("value must contain finite JSON data") from error
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def content_sha256(record: dict[str, Any]) -> str:
    """Bind reviewed text, source provenance, and applicability scope together."""
    return json_sha256({key: record[key] for key in
                        ("text", "sources", "scope", "content_type", "supersedes") if key in record})


def record_sha256(record: dict[str, Any]) -> str:
    """Hash a snapshot without its audit pointer, avoiding a circular event hash."""
    return json_sha256({key: value for key, value in record.items() if key != "audit_head"})


def _string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _sha256(value: Any, field: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{field} must be a lowercase SHA-256")


def _date(value: Any, field: str) -> date:
    _string(value, field)
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError()
        return parsed
    except ValueError as error:
        raise ValueError(f"{field} must be a YYYY-MM-DD date") from error


def timestamp(value: Any, field: str = "at") -> datetime:
    _string(value, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError()
        return parsed
    except ValueError as error:
        raise ValueError(f"{field} must be a timezone-aware ISO timestamp") from error


def _fields(value: Any, expected: set[str], label: str,
            optional: set[str] | None = None) -> None:
    allowed = expected | (optional or set())
    if (not isinstance(value, dict) or not expected.issubset(value)
            or not set(value).issubset(allowed)):
        raise ValueError(f"{label} is missing required fields or has unknown fields: {', '.join(sorted(expected))}")


def validate_record(record: Any) -> None:
    """Raise ValueError for unsupported, malformed, or content-altered records."""
    _fields(record, set(KnowledgeRecord.__required_keys__), "knowledge record",
            set(KnowledgeRecord.__optional_keys__))
    if type(record["schema_version"]) is not int or record["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported knowledge schema_version")
    if type(record["revision"]) is not int or record["revision"] < 1:
        raise ValueError("revision must be a positive integer")
    for field in ("record_id", "text", "created_by"):
        _string(record[field], field)
    for field in ("content_type", "supersedes"):
        if field in record:
            _string(record[field], field)
    if record.get("supersedes") == record["record_id"]:
        raise ValueError("a record cannot supersede itself")
    if not isinstance(record["status"], str) or record["status"] not in STATUSES:
        raise ValueError("unknown knowledge status")
    _sha256(record["text_sha256"], "text_sha256")
    if hashlib.sha256(record["text"].encode("utf-8")).hexdigest() != record["text_sha256"]:
        raise ValueError("text_sha256 does not match the exact text")
    _sha256(record["audit_head"], "audit_head")
    created = timestamp(record["created_at"], "created_at")
    updated = timestamp(record["updated_at"], "updated_at")
    if updated < created:
        raise ValueError("updated_at cannot precede created_at")
    if not isinstance(record["scope"], dict) or not record["scope"]:
        raise ValueError("scope must be a non-empty JSON object")
    if any(not isinstance(key, str) or not key.strip() for key in record["scope"]):
        raise ValueError("scope keys must be non-empty strings")
    # Round-trip equality also rejects tuples and non-string nested object keys.
    json_sha256(record["scope"])
    if json.loads(json.dumps(record["scope"])) != record["scope"]:
        raise ValueError("scope must contain JSON values")
    if not isinstance(record["sources"], list) or not record["sources"]:
        raise ValueError("sources must be a non-empty list")
    source_ids = set()
    for source in record["sources"]:
        _fields(source, set(SourceReference.__required_keys__), "source reference",
                set(SourceReference.__optional_keys__))
        for field in ("source_id", "url", "title", "publisher", "locator"):
            _string(source[field], f"source.{field}")
        try:
            url = urlsplit(source["url"])
            if (url.scheme != "https" or not url.hostname
                    or url.username is not None or url.password is not None):
                raise ValueError()
        except ValueError as error:
            raise ValueError("source.url must be an HTTPS URL without credentials") from error
        _date(source["accessed_at"], "source.accessed_at")
        for field in ("edition", "version", "section", "license", "snapshot_ref",
                      "license_status", "license_attribution", "license_evidence_ref",
                      "license_evidence_sha256"):
            if field in source:
                _string(source[field], f"source.{field}")
        for field in ("publication_date", "valid_from", "valid_until"):
            if field in source:
                _date(source[field], f"source.{field}")
        if ("valid_from" in source and "valid_until" in source
                and source["valid_until"] < source["valid_from"]):
            raise ValueError("source.valid_until cannot precede source.valid_from")
        if (record["status"] in {"APPROVED", "PUBLISHED"}
                and "valid_until" in source and date.today().isoformat() > source["valid_until"]):
            raise ValueError("expired source cannot be approved or published")
        if "page" in source:
            if isinstance(source["page"], str):
                _string(source["page"], "source.page")
            elif type(source["page"]) is not int or source["page"] < 1:
                raise ValueError("source.page must be a positive integer or non-empty string")
        if "snapshot_sha256" in source:
            _sha256(source["snapshot_sha256"], "source.snapshot_sha256")
        if "license_evidence_sha256" in source:
            _sha256(source["license_evidence_sha256"], "source.license_evidence_sha256")
        if "license_status" in source:
            from tools.source_snapshots import validate_license_status, validate_locator
            validate_license_status(source["license_status"])
            if source.get("license_status") == "ATTRIBUTION_REQUIRED" and not source.get("license_attribution"):
                raise ValueError("attribution-required source must define attribution text")
            if "evidence_locator" in source:
                validate_locator(source["evidence_locator"])
        if record["status"] in {"APPROVED", "PUBLISHED"} and (
                not source.get("snapshot_ref") or not source.get("snapshot_sha256")):
            raise ValueError("approved/published sources require immutable snapshot provenance")
        if record["status"] in {"APPROVED", "PUBLISHED"}:
            from tools.human_review import ALLOWED_PUBLICATION_LICENSES
            from tools.source_snapshots import validate_locator
            if source.get("license_status") not in ALLOWED_PUBLICATION_LICENSES:
                raise ValueError("approved/published sources require a compatible explicit license decision")
            if not source.get("license_evidence_ref"):
                raise ValueError("approved/published sources require a license evidence reference")
            if not source.get("license_evidence_sha256"):
                raise ValueError("approved/published sources require a license evidence hash")
            validate_locator(source.get("evidence_locator"))
        if source["source_id"] in source_ids:
            raise ValueError("source_id must be unique within a record")
        source_ids.add(source["source_id"])
    approval = record["approval"]
    if approval is None:
        if record["status"] in {"APPROVED", "PUBLISHED"}:
            raise ValueError("APPROVED/PUBLISHED require explicit approval evidence")
        return
    if record["status"] not in {"APPROVED", "PUBLISHED", "DEPRECATED"}:
        raise ValueError("approval is only valid for approved, published, or deprecated records")
    _fields(approval, set(Approval.__annotations__), "approval")
    for field in ("review_id", "approver_id"):
        _string(approval[field], f"approval.{field}")
    reviewer_ids = approval["reviewer_ids"]
    if (not isinstance(reviewer_ids, list) or len(reviewer_ids) < 2
            or any(not isinstance(value, str) or not value.strip() for value in reviewer_ids)):
        raise ValueError("approval requires distinct explicit reviewer_ids")
    reviewers = {value.strip().casefold() for value in reviewer_ids}
    if (len(reviewers) != len(reviewer_ids)
            or approval["approver_id"].strip().casefold() in reviewers
            or approval["approver_type"] != "human"):
        raise ValueError("approval requires a distinct explicit human approver")
    reviewed = _date(approval["reviewed_at"], "approval.reviewed_at")
    approved = timestamp(approval["approved_at"], "approval.approved_at")
    if approved < created or approved > updated or reviewed > approved.date():
        raise ValueError("approval dates are inconsistent with the record")
    _sha256(approval["content_sha256"], "approval.content_sha256")
    _sha256(approval["review_entry_sha256"], "approval.review_entry_sha256")
    if approval["content_sha256"] != content_sha256(record):
        raise ValueError("approval does not cover current content, sources, and scope")


def validate_audit_event(event: Any) -> None:
    """Validate an immutable event's shape and hash, without asserting identity."""
    _fields(event, set(AuditEvent.__annotations__), "audit event")
    if type(event["schema_version"]) is not int or event["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported audit schema_version")
    if type(event["revision"]) is not int or event["revision"] < 1:
        raise ValueError("audit revision must be a positive integer")
    for field in ("event_id", "record_id", "actor_id", "reason"):
        _string(event[field], field)
    if (not isinstance(event["to_status"], str) or event["to_status"] not in STATUSES
            or event["from_status"] is not None and (
                not isinstance(event["from_status"], str) or event["from_status"] not in STATUSES)):
        raise ValueError("unknown audit status")
    if not isinstance(event["actor_type"], str) or event["actor_type"] not in {"human", "agent", "system"}:
        raise ValueError("unknown actor_type")
    timestamp(event["at"])
    for field in ("after_sha256", "event_sha256"):
        _sha256(event[field], field)
    for field in ("before_sha256", "previous_event_sha256"):
        if event[field] is not None:
            _sha256(event[field], field)
    if event["event_sha256"] != json_sha256({
        key: value for key, value in event.items() if key != "event_sha256"
    }):
        raise ValueError("audit event hash mismatch")
