"""Structural source, review, and vector-runtime contracts; no crop facts."""

import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools.human_review import (
    build_review_package, promotion_blockers, validate_conflict, validate_human_review,
)
from tools.retrieval_runtime import (
    build_index_manifest, embedding_artifact_hash, validate_embedding_manifest,
    validate_index_manifest,
)
from tools.source_snapshots import (
    capture_snapshot, source_changed, validate_locator, verify_snapshot, write_public_manifest,
)
from tools.knowledge_lifecycle import new_record
from tools.knowledge_schema import validate_record


class SourceSnapshotTests(unittest.TestCase):
    def capture(self, root, content=b"synthetic source bytes", at="2026-09-30T12:00:00+00:00"):
        return capture_snapshot(
            source_id="TEST-SOURCE", original_url="https://example.org/source",
            content=content, mime_type="text/plain", document_title="Synthetic source",
            institution="Synthetic publisher", retrieved_at=at, storage_root=root)

    def test_snapshot_is_content_addressed_and_changed_bytes_are_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self.capture(root)
            again = self.capture(root, at="2026-10-01T12:00:00+00:00")
            changed = self.capture(root, b"changed source bytes")
            self.assertEqual(first["content_hash"], again["content_hash"])
            self.assertTrue(verify_snapshot(first, storage_root=root))
            self.assertTrue(source_changed(first, b"changed source bytes"))
            self.assertEqual(changed["snapshot_status"], "CHANGED_SINCE_PRIOR_SNAPSHOT")

    def test_snapshot_tampering_and_path_escape_fail_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = self.capture(root)
            (root / snapshot["local_path"]).write_bytes(b"tampered")
            self.assertFalse(verify_snapshot(snapshot, storage_root=root))
            with self.assertRaisesRegex(ValueError, "content-addressed snapshot is corrupted"):
                self.capture(root)
            snapshot["local_path"] = "../outside"
            self.assertFalse(verify_snapshot(snapshot, storage_root=root))

    def test_public_metadata_manifest_is_content_addressed_and_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = self.capture(root)
            manifest = write_public_manifest(snapshot, manifest_root=root / "public")
            self.assertTrue(manifest.is_file())
            self.assertEqual(write_public_manifest(snapshot, manifest_root=root / "public"), manifest)
            changed = dict(snapshot, institution="Changed metadata")
            with self.assertRaisesRegex(ValueError, "immutable"):
                write_public_manifest(changed, manifest_root=root / "public")

    def test_locator_requires_stable_identifier_and_valid_page_range(self):
        validate_locator({"page_start": 2, "page_end": 3, "section": "Methods"})
        for invalid in ({"quote": "only a quote"}, {"page_start": 4, "page_end": 2},
                        {"table": "", "quote_hash": "bad"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_locator(invalid)


class HumanReviewGateTests(unittest.TestCase):
    def fixture(self):
        snapshot = {"content_hash": "a" * 64, "snapshot_id": "S:a"}
        candidate = {"candidate_id": "TEST", "claim": "synthetic claim",
                     "context": {"crop": "synthetic"}, "risk_level": "LOW"}
        content_hash = hashlib.sha256(json.dumps(candidate, sort_keys=True,
                            separators=(",", ":")).encode()).hexdigest()
        review = {
            "reviewer_id": "qualified-person", "reviewer_role": "agronomic-reviewer",
            "qualification": "externally verified reference", "reviewed_at": "2026-09-30",
            "decision": "APPROVE", "scope": {"crop": "synthetic"},
            "comments": "synthetic structural test", "source_snapshot_hash": "a" * 64,
            "candidate_content_hash": content_hash, "limitations": [],
        }
        return candidate, snapshot, content_hash, review

    def test_package_marks_ai_notes_as_nonhuman_and_suggestion_only(self):
        candidate, snapshot, _content, _review = self.fixture()
        package = build_review_package(candidate, snapshot=snapshot,
            locator={"page": 1, "section": "Synthetic"}, exact_evidence="synthetic evidence",
            ai_reviewer_notes=["not an agronomic conclusion"])
        self.assertTrue(package["decision_is_suggestion_only"])
        self.assertTrue(package["ai_reviewer_notes"][0]["not_human_review"])

    def test_promotion_gate_requires_all_independent_gates(self):
        candidate, snapshot, content_hash, review = self.fixture()
        blockers = promotion_blockers(
            snapshot=snapshot, snapshot_valid=True, locator={"page": 1, "section": "Synthetic"},
            license_status="REDISTRIBUTION_ALLOWED", schema_valid=True,
            scope=candidate["context"], human_review=review, candidate_hash=content_hash,
            conflict_blocking=False, deprecated=False,
            license_evidence_ref="synthetic-test-only", license_evidence_valid=True,
            today=date(2026, 9, 30))
        self.assertEqual(blockers, [])
        blockers = promotion_blockers(
            snapshot=snapshot, snapshot_valid=False, locator=None, license_status="UNKNOWN",
            schema_valid=True, scope=candidate["context"], human_review=None,
            candidate_hash=content_hash, conflict_blocking=True, deprecated=False)
        self.assertIn("SOURCE_SNAPSHOT_INVALID_OR_CHANGED", blockers)
        self.assertIn("LICENSE_POLICY_BLOCKS_PUBLICATION", blockers)
        self.assertIn("HUMAN_REVIEW_MISSING", blockers)
        self.assertIn("UNRESOLVED_EVIDENCE_CONFLICT", blockers)
        self.assertIn("LICENSE_EVIDENCE_MISSING", blockers)
        invalid_license_evidence = promotion_blockers(
            snapshot=snapshot, snapshot_valid=True, locator={"page": 1},
            license_status="REDISTRIBUTION_ALLOWED", license_evidence_ref="license.json",
            license_evidence_valid=False, schema_valid=True, scope=candidate["context"],
            human_review=review, candidate_hash=content_hash,
            conflict_blocking=False, deprecated=False)
        self.assertIn("LICENSE_EVIDENCE_INVALID", invalid_license_evidence)

    def test_changed_content_or_snapshot_invalidates_review(self):
        candidate, _snapshot, content_hash, review = self.fixture()
        with self.assertRaisesRegex(ValueError, "different candidate content"):
            validate_human_review(review, candidate_hash="b" * 64,
                                  snapshot_hash="a" * 64, scope=candidate["context"])
        with self.assertRaisesRegex(ValueError, "different source snapshot"):
            validate_human_review(review, candidate_hash=content_hash,
                                  snapshot_hash="b" * 64, scope=candidate["context"])

    def test_conflict_schema_keeps_ai_disagreement_unresolved(self):
        conflict = {
            "conflict_id": "TEST-CONFLICT", "candidate_id": "TEST",
            "source_a": "SAME-SOURCE", "source_b": "SAME-SOURCE",
            "difference_type": "AI_REVIEW_DISAGREEMENT", "scope_difference": None,
            "publication_date_difference": None, "regional_difference": None,
            "methodological_difference": None, "unresolved_question": "Synthetic review question",
            "resolution_status": "UNRESOLVED",
        }
        validate_conflict(conflict)
        conflict["resolution_status"] = "RESOLVED_BY_MAJORITY"
        with self.assertRaises(ValueError):
            validate_conflict(conflict)

    def test_conflict_inventory_has_five_unresolved_disagreements(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "tests/agronomic_candidate_conflicts.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["conflicts"]), 5)
        for conflict in data["conflicts"]:
            validate_conflict(conflict)

    def test_lifecycle_record_cannot_be_approved_without_compatible_license_locator(self):
        source = {
            "source_id": "SYNTHETIC", "url": "https://example.org/source",
            "title": "Synthetic", "publisher": "Synthetic", "locator": "fixture",
            "accessed_at": "2026-09-30", "snapshot_ref": "snapshot",
            "snapshot_sha256": "a" * 64,
        }
        record, _ = new_record("synthetic", "synthetic text", [source], {"crop": "synthetic"},
                               actor_id="test", at="2026-09-30T12:00:00+00:00")
        record["status"] = "APPROVED"
        with self.assertRaisesRegex(ValueError, "explicit license decision"):
            validate_record(record)


class IndexCompatibilityTests(unittest.TestCase):
    def test_model_identifier_alone_never_triggers_automatic_download(self):
        from tools.vector_db import LocalVectorDB
        with self.assertRaisesRegex(RuntimeError, "automatic model downloads are disabled"):
            LocalVectorDB(model_name="organization/model-id")

    def test_index_hash_release_model_revision_and_dimension_are_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "faiss.index").write_bytes(b"synthetic index")
            (root / "metadata.json").write_text(json.dumps([{"id": "synthetic"}]))
            model = {"model_id": "example/model", "revision": "commit-sha",
                     "expected_dimension": 4, "artifact_origin": "local test fixture",
                     "artifact_hash": "a" * 64}
            manifest = build_index_manifest(index_path=root, index_type="test",
                embedding_model=model, knowledge_release="release-1", record_count=1, dimension=4)
            (root / "index_manifest.json").write_text(json.dumps(manifest))
            validate_index_manifest(root, expected_release="release-1",
                                    expected_model="example/model", expected_revision="commit-sha",
                                    expected_dimension=4)
            with self.assertRaisesRegex(ValueError, "release mismatch"):
                validate_index_manifest(root, expected_release="release-2")
            with self.assertRaisesRegex(ValueError, "model mismatch"):
                validate_index_manifest(root, expected_release="release-1", expected_model="wrong/model")
            with self.assertRaisesRegex(ValueError, "revision mismatch"):
                validate_index_manifest(root, expected_release="release-1", expected_revision="wrong-revision")
            with self.assertRaisesRegex(ValueError, "dimension mismatch"):
                validate_index_manifest(root, expected_release="release-1", expected_dimension=3)
            (root / "faiss.index").write_bytes(b"corrupt index")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                validate_index_manifest(root, expected_release="release-1")
            (root / "faiss.index").write_bytes(b"synthetic index")
            (root / "index_manifest.json").write_text("{corrupt", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                validate_index_manifest(root, expected_release="release-1")

    def test_wrong_embedding_dimension_rejected_at_manifest_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "faiss.index").write_bytes(b"index")
            (root / "metadata.json").write_text("[]")
            model = {"model_id": "m", "revision": "r", "expected_dimension": 8,
                     "artifact_origin": "local", "artifact_hash": "b" * 64}
            with self.assertRaisesRegex(ValueError, "dimension"):
                build_index_manifest(index_path=root, index_type="test", embedding_model=model,
                    knowledge_release="release", record_count=0, dimension=4)

    def test_embedding_artifact_manifest_binds_local_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "config.json").write_text('{"model": "synthetic"}', encoding="utf-8")
            manifest = {"model_id": "synthetic/model", "revision": "immutable-rev",
                        "expected_dimension": 4, "artifact_origin": "test fixture",
                        "artifact_hash": embedding_artifact_hash(root)}
            self.assertEqual(validate_embedding_manifest(manifest, root), manifest)
            (root / "config.json").write_text('{"model": "changed"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "artifact hash"):
                validate_embedding_manifest(manifest, root)


if __name__ == "__main__":
    unittest.main()
