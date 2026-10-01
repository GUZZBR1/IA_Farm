"""Synthetic structural fixtures only; these tests contain no agronomic facts."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.knowledge_lifecycle import new_record, transition_record, validate_audit_chain
from tools.knowledge_schema import content_sha256, validate_audit_event, validate_record
from tools.knowledge_release import validate_published_authority
from tools.review_verifier import compare_reviews


AT = "2026-01-02T12:00:00+00:00"
TEXT = "Synthetic reviewed text for a lifecycle contract test."
SOURCE = {
    "source_id": "TEST-SOURCE", "url": "https://www.embrapa.br/synthetic-test",
    "title": "Synthetic source", "publisher": "Synthetic publisher",
    "locator": "Synthetic section", "accessed_at": "2026-01-01",
    "snapshot_ref": "source-snapshot.txt",
    "snapshot_sha256": hashlib.sha256(b"Synthetic source snapshot for a contract test.").hexdigest(),
}


def external_review(root, record):
    """Write structural fake reviews/signoff; no factual or qualified approval."""
    (root / SOURCE["snapshot_ref"]).write_bytes(b"Synthetic source snapshot for a contract test.")
    def artifact(name, payload):
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    frozen = artifact("input.json", {
        "sources": [{"id": SOURCE["source_id"], "url": SOURCE["url"],
                     "snapshot_ref": SOURCE["snapshot_ref"], "snapshot_sha256": SOURCE["snapshot_sha256"]}],
        "cases": [{"id": "TEST-REVIEW", "context": {"crop": "synthetic"},
                   "source_ids": [SOURCE["source_id"]]}],
    })
    evidence = {key: SOURCE[key] for key in
                ("url", "title", "publisher", "locator", "accessed_at")}
    evidence.update({"source_type": "official_research", "edition_or_validity": "synthetic",
                     "evidence": "Synthetic evidence for the test.", "claim_ids": ["TEST-CLAIM"]})
    reports = []
    for role in ("maize_evidence_specialist", "independent_verifier"):
        reports.append({
            "reviewer_role": role, "reviewed_at": "2026-01-02",
            "reviewer_id": "test-reviewer" if role == "maize_evidence_specialist" else "test-verifier",
            "run_report": frozen["path"], "run_report_sha256": frozen["sha256"],
            "reviews": [{"review_id": "TEST-REVIEW", "text_sha256": record["text_sha256"],
                         "verdict": "correct", "evidence_basis": "primary_source",
                         "source_supported": True, "scope_correct": True,
                         "critical_error": False, "rationale": "Synthetic test rationale.",
                         "sources": [evidence]}],
        })
    return {
        "record_id": record["record_id"], "review_id": "TEST-REVIEW",
        "approval_status": "approved", "text_sha256": record["text_sha256"],
        "approved_content_sha256": content_sha256(record),
        "source_id": SOURCE["source_id"], "crop": "synthetic", "review_date": "2026-01-02",
        "reviewer_ids": ["maize_evidence_specialist", "independent_verifier"],
        "approver_id": "test-approver", "approver_type": "human",
        "source_snapshots": [{"source_id": SOURCE["source_id"], "path": SOURCE["snapshot_ref"],
                              "sha256": SOURCE["snapshot_sha256"]}],
        # This fake signoff exercises structure only. It is not a real human or
        # qualified agronomist's approval and is never persisted in project data.
        "human_approval": artifact("test-only-human-signoff.json", {
            "schema_version": 1, "decision": "approve", "approver_type": "human",
            "approver_id": "test-approver", "approver_role": "qualified_agronomic_reviewer",
            "qualification_reference": "TEST-ONLY-STRUCTURAL-FAKE-NOT-A-CREDENTIAL",
            "approved_at": "2026-01-02", "record_id": record["record_id"], "review_id": "TEST-REVIEW",
            "text_sha256": record["text_sha256"], "source_id": SOURCE["source_id"],
            "crop": "synthetic", "review_input_sha256": frozen["sha256"],
            "source_snapshot_sha256": SOURCE["snapshot_sha256"],
            "content_sha256": content_sha256(record),
        }),
        "review_input": frozen,
        "review_artifacts": {"specialist": artifact("specialist.json", reports[0]),
                             "verifier": artifact("verifier.json", reports[1])},
        "comparison_artifact": artifact("comparison.json", compare_reviews(*reports)),
    }


class KnowledgeLifecycleTests(unittest.TestCase):
    def raw(self):
        return new_record("TEST-RECORD", TEXT, [SOURCE], {"crop": "synthetic"},
                          actor_id="test-ingest", at=AT)

    def under_review(self):
        record, event = self.raw()
        events = [event]
        for target in ("PARSED", "CANDIDATE", "UNDER_REVIEW"):
            record, event = transition_record(record, target, actor_id="test-curator",
                                             reason="Synthetic stage transition.", at=AT)
            events.append(event)
        return record, events

    def test_creation_is_raw_detached_json_and_has_valid_audit_head(self):
        sources = [copy.deepcopy(SOURCE)]
        scope = {"crop": "synthetic"}
        record, event = new_record("TEST-RECORD", TEXT, sources, scope,
                                   actor_id="test-ingest", at=AT)
        sources[0]["title"] = "changed input"
        scope["crop"] = "changed input"
        self.assertEqual(record["status"], "RAW")
        self.assertIsNone(record["approval"])
        self.assertEqual(record["sources"][0]["title"], SOURCE["title"])
        self.assertEqual(record["scope"], {"crop": "synthetic"})
        validate_audit_chain([event], json.loads(json.dumps(record)))

    def test_direct_publication_and_approval_skips_are_blocked(self):
        record, _ = self.raw()
        for target in ("PUBLISHED", "APPROVED", "UNDER_REVIEW", "RAW", "unknown"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                transition_record(record, target, actor_id="test-human", actor_type="human",
                                  reason="Attempt shortcut.", at=AT)

    def test_self_asserted_approval_has_no_transition_authority(self):
        record, _ = self.under_review()
        with self.assertRaises(ValueError):
            transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                              reason="Explicit decision.", at=AT)
        with self.assertRaises(ValueError):
            transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                              reason="Explicit decision.", at=AT,
                              review_entry={"approval_status": "approved"})

    def test_review_artifacts_and_distinct_human_approval_required(self):
        record, events = self.under_review()
        before = copy.deepcopy(record)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            review = external_review(root, record)
            options = dict(actor_id="test-approver", reason="Explicit test human decision.",
                           at=AT, review_entry=review, base_dir=root)
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", **options)
            same_person = copy.deepcopy(review)
            same_person["reviewer_ids"] = [" TEST-APPROVER ", "independent_verifier"]
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", **dict(options, actor_type="human",
                                                            review_entry=same_person))
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", **dict(options, actor_type="human",
                                                            actor_id="another-human"))
            approved, event = transition_record(record, "APPROVED", actor_type="human", **options)
            self.assertEqual(record, before)
            self.assertEqual(approved["approval"]["approver_id"], "test-approver")
            self.assertEqual(approved["revision"], record["revision"] + 1)
            events.append(event)
            published, event = transition_record(approved, "PUBLISHED", actor_type="human", **options)
            self.assertEqual(published["approval"], approved["approval"])
            self.assertEqual(published["status"], "PUBLISHED")
            events.append(event)
            validate_audit_chain(events, published)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps({"schema_version": 2, "entries": [review]}),
                                     encoding="utf-8")
            validate_published_authority([published], registry_path, root)
            # Recomputing the record-local checksum cannot broaden human-approved scope.
            altered_scope = copy.deepcopy(published)
            altered_scope["scope"]["region"] = "unreviewed-region"
            altered_scope["approval"]["content_sha256"] = content_sha256(altered_scope)
            with self.assertRaises(ValueError):
                validate_published_authority([altered_scope], registry_path, root)
            # Publication revalidates the artifacts; a hash copied into metadata is insufficient.
            (root / "specialist.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                transition_record(approved, "PUBLISHED", actor_type="human", **options)

    def test_publication_cannot_substitute_the_approval_entry(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            options = dict(actor_id="test-approver", actor_type="human", reason="Explicit decision.",
                           at=AT, review_entry=entry, base_dir=root)
            approved, _ = transition_record(record, "APPROVED", **options)
            changed = copy.deepcopy(entry)
            changed["reviewer_ids"] = ["another-reviewer", "independent_verifier"]
            with self.assertRaises(ValueError):
                transition_record(approved, "PUBLISHED", **dict(options, review_entry=changed))
            with self.assertRaises(ValueError):
                transition_record(approved, "PUBLISHED", **dict(options, actor_type="agent"))

    def test_human_artifact_is_required_and_cannot_be_substituted_by_entry_fields(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            options = dict(actor_id="test-approver", actor_type="human", reason="Explicit decision.",
                           at=AT, review_entry=entry, base_dir=root)
            missing = copy.deepcopy(entry)
            del missing["human_approval"]
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", **dict(options, review_entry=missing))
            substituted = dict(entry, approver_id="another-human")
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", **dict(options, actor_id="another-human",
                                                            review_entry=substituted))
            signoff_path = root / entry["human_approval"]["path"]
            signoff = json.loads(signoff_path.read_text(encoding="utf-8"))
            signoff["approved_at"] = "2026-01-03"
            signoff_path.write_text(json.dumps(signoff), encoding="utf-8")
            updated = copy.deepcopy(entry)
            updated["human_approval"]["sha256"] = hashlib.sha256(signoff_path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", **dict(options, review_entry=updated))

    def test_external_review_must_cover_source_urls_and_scope(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            for change in ("url", "scope"):
                changed = copy.deepcopy(record)
                if change == "url":
                    changed["sources"][0]["url"] = "https://www.embrapa.br/different-synthetic-source"
                else:
                    changed["scope"]["region"] = "unreviewed synthetic region"
                with self.subTest(change=change), self.assertRaises(ValueError):
                    transition_record(changed, "APPROVED", actor_id="test-approver", actor_type="human",
                                      reason="Explicit decision.", at=AT, review_entry=entry, base_dir=root)

    def test_source_references_without_ingested_snapshots_cannot_be_approved(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            for omitted in ("snapshot_ref", "snapshot_sha256"):
                changed = copy.deepcopy(record)
                del changed["sources"][0][omitted]
                validate_record(changed)
                with self.subTest(omitted=omitted), self.assertRaises(ValueError):
                    transition_record(changed, "APPROVED", actor_id="test-approver", actor_type="human",
                                      reason="Explicit decision.", at=AT, review_entry=entry, base_dir=root)
            (root / SOURCE["snapshot_ref"]).unlink()
            with self.assertRaises(ValueError):
                transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                                  reason="Explicit decision.", at=AT, review_entry=entry, base_dir=root)

    def test_publication_rechecks_snapshot_bytes_and_approval_binding(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            options = dict(actor_id="test-approver", actor_type="human", reason="Explicit decision.",
                           at=AT, review_entry=entry, base_dir=root)
            approved, _ = transition_record(record, "APPROVED", **options)
            (root / SOURCE["snapshot_ref"]).write_bytes(b"Altered synthetic snapshot.")
            with self.assertRaises(ValueError):
                transition_record(approved, "PUBLISHED", **options)
            changed = copy.deepcopy(approved)
            changed["sources"][0]["snapshot_sha256"] = hashlib.sha256(b"Altered synthetic snapshot.").hexdigest()
            with self.assertRaises(ValueError):
                validate_record(changed)

    def test_optional_source_provenance_and_validity_dates_are_validated(self):
        record, _ = self.raw()
        source = record["sources"][0]
        source.update({"edition": "Synthetic edition", "version": "1", "page": 2,
                       "section": "Synthetic section", "license": "Synthetic test license",
                       "publication_date": "2026-01-01", "valid_from": "2026-01-01",
                       "valid_until": "2026-12-31"})
        validate_record(record)
        for field, value in (("page", False), ("page", 0), ("publication_date", "not-a-date"),
                             ("valid_until", "2025-12-31"), ("snapshot_sha256", "not-a-hash")):
            changed = copy.deepcopy(record)
            changed["sources"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_record(changed)

    def test_snapshot_provenance_must_match_the_external_review_entry(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            for field, value in (("source_id", "another-source"), ("path", "different-snapshot.txt"),
                                 ("sha256", "0" * 64)):
                changed = copy.deepcopy(entry)
                changed["source_snapshots"][0][field] = value
                with self.subTest(field=field), self.assertRaises(ValueError):
                    transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                                      reason="Explicit decision.", at=AT, review_entry=changed, base_dir=root)
            for snapshots in ([], entry["source_snapshots"] * 2):
                changed = dict(entry, source_snapshots=snapshots)
                with self.assertRaises(ValueError):
                    transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                                      reason="Explicit decision.", at=AT, review_entry=changed, base_dir=root)

    def test_optional_content_type_and_supersession_are_supported(self):
        record, event = new_record("TEST-NEW", TEXT, [SOURCE], {"crop": "synthetic"},
                                   actor_id="test-ingest", at=AT,
                                   content_type="synthetic_reference", supersedes="TEST-OLD")
        self.assertEqual(record["content_type"], "synthetic_reference")
        self.assertEqual(record["supersedes"], "TEST-OLD")
        validate_audit_chain([event], record)
        with self.assertRaises(ValueError):
            new_record("TEST-NEW", TEXT, [SOURCE], {"crop": "synthetic"},
                       actor_id="test-ingest", at=AT, supersedes="TEST-NEW")

    def test_approved_content_provenance_and_scope_cannot_be_changed(self):
        record, _ = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            approved, _ = transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                                             reason="Explicit decision.", at=AT, review_entry=entry, base_dir=root)
            for field in ("text", "sources", "scope"):
                changed = copy.deepcopy(approved)
                if field == "text":
                    changed["text"] += " Altered."
                    changed["text_sha256"] = hashlib.sha256(changed["text"].encode()).hexdigest()
                elif field == "sources":
                    changed["sources"][0]["locator"] = "Another section"
                else:
                    changed["scope"]["crop"] = "changed synthetic scope"
                with self.subTest(field=field), self.assertRaises(ValueError):
                    validate_record(changed)

    def test_reopening_requires_new_approval_and_deprecation_stops_publication(self):
        record, events = self.under_review()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = external_review(root, record)
            approved, event = transition_record(record, "APPROVED", actor_id="test-approver", actor_type="human",
                                                reason="Explicit decision.", at=AT, review_entry=entry, base_dir=root)
            events.append(event)
            reopened, _ = transition_record(approved, "UNDER_REVIEW", actor_id="test-curator",
                                             reason="Request another review.", at=AT)
            self.assertIsNone(reopened["approval"])
            with self.assertRaises(ValueError):
                transition_record(reopened, "PUBLISHED", actor_id="test-approver", actor_type="human",
                                  reason="Premature publication.", at=AT, review_entry=entry, base_dir=root)
            deprecated, event = transition_record(approved, "DEPRECATED", actor_id="test-curator",
                                                 reason="Withdraw test record.", at=AT)
            events.append(event)
            validate_audit_chain(events, deprecated)
            with self.assertRaises(ValueError):
                transition_record(deprecated, "PUBLISHED", actor_id="test-approver", actor_type="human",
                                  reason="Republish withdrawn record.", at=AT, review_entry=entry, base_dir=root)

    def test_audit_chain_detects_mutation_reordering_truncation_and_wrong_snapshot(self):
        record, events = self.under_review()
        validate_audit_chain(events, record)
        changed = copy.deepcopy(events[0])
        changed["reason"] = "Forged reason"
        with self.assertRaises(ValueError):
            validate_audit_event(changed)
        for broken in ([], events[1:], events[:-1], [events[0], events[2], events[1], events[3]]):
            with self.subTest(length=len(broken)), self.assertRaises(ValueError):
                validate_audit_chain(broken, record)
        wrong_snapshot = copy.deepcopy(record)
        wrong_snapshot["created_by"] = "forged-creator"
        with self.assertRaises(ValueError):
            validate_audit_chain(events, wrong_snapshot)

    def test_schema_versions_timestamps_and_invalid_json_are_rejected(self):
        record, _ = self.raw()
        changes = {
            "schema_version": 2, "revision": True, "status": [],
            "updated_at": "2026-01-02", "approval": {"approved": True},
            "scope": {"nonfinite": float("nan")},
        }
        for field, value in changes.items():
            changed = copy.deepcopy(record)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_record(changed)
        with self.assertRaises(ValueError):
            transition_record(record, "PARSED", actor_id="test-curator", reason="", at=AT)
        with self.assertRaises(ValueError):
            transition_record(record, "PARSED", actor_id="test-curator", reason="Parse text.",
                              at="2026-01-01T12:00:00+00:00")

    def test_malformed_audit_status_and_actor_types_fail_as_validation_errors(self):
        record, event = self.raw()
        for field in ("from_status", "to_status", "actor_type"):
            changed = copy.deepcopy(event)
            changed[field] = []
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_audit_event(changed)
        with self.assertRaises(ValueError):
            transition_record(record, "PARSED", actor_id="test-curator", actor_type=[],
                              reason="Parse text.", at=AT)


if __name__ == "__main__":
    unittest.main()
