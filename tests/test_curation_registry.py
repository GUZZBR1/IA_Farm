import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.curation_registry import CurationRegistry, text_sha256
from tools.review_verifier import compare_reviews


class CurationRegistryTests(unittest.TestCase):
    def test_duplicate_record_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            duplicate = {"record_id": "DUPLICATE"}
            path.write_text(json.dumps({"schema_version": 2, "entries": [duplicate, duplicate]}),
                            encoding="utf-8")
            registry = CurationRegistry(path)
            self.assertEqual(registry.entries, {})

    def test_registry_accepts_exactly_bound_independent_reviews(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            excerpt = "A reviewed exact excerpt."
            review_id = "CASE-001"
            candidates = {
                "sources": [{"id": "SOURCE-1", "url": "https://www.embrapa.br/example"}],
                "cases": [{"id": review_id, "context": {"crop": "maize"},
                           "source_ids": ["SOURCE-1"]}]
            }
            input_path = root / "candidates.json"
            input_path.write_text(json.dumps(candidates), encoding="utf-8")
            input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
            source_snapshot_path = root / "source.snapshot"
            source_snapshot_path.write_text(
                "TEST FIXTURE ONLY; this is not a source of agronomic information.",
                encoding="utf-8",
            )
            source_snapshot_hash = hashlib.sha256(source_snapshot_path.read_bytes()).hexdigest()
            source = {
                "url": "https://www.embrapa.br/example",
                "title": "Official source", "publisher": "Embrapa",
                "source_type": "official_research", "edition_or_validity": "2026",
                "accessed_at": "2026-01-01", "locator": "section 1",
                "evidence": "Supports the reviewed claim.", "claim_ids": ["C1"],
            }

            def write_review(role):
                label = "specialist" if role == "maize_evidence_specialist" else "verifier"
                report = {
                    "reviewer_role": role, "reviewed_at": "2026-01-02",
                    "run_report": input_path.name, "run_report_sha256": input_hash,
                    "reviews": [{
                        "review_id": review_id, "text_sha256": text_sha256(excerpt),
                        "verdict": "correct", "evidence_basis": "primary_source",
                        "source_supported": True, "scope_correct": True,
                        "critical_error": False, "rationale": "Evidence supports claim.",
                        "sources": [source],
                    }],
                }
                path = root / f"{label}.json"
                path.write_text(json.dumps(report), encoding="utf-8")
                return path, report

            specialist_path, specialist = write_review("maize_evidence_specialist")
            verifier_path, verifier = write_review("independent_verifier")
            comparison = compare_reviews(specialist, verifier)
            comparison_path = root / "comparison.json"
            comparison_path.write_text(json.dumps(comparison), encoding="utf-8")
            artifact = lambda path: {
                "path": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            entry = {
                "record_id": "CURATED-001", "review_id": review_id,
                "approval_status": "approved", "text_sha256": text_sha256(excerpt),
                "source_id": "SOURCE-1", "crop": "maize", "review_date": "2026-01-02",
                "reviewer_ids": ["maize_evidence_specialist", "independent_verifier"],
                "approver_id": "test-human-reviewer", "approver_type": "human",
                "approved_content_sha256": "a" * 64,
                "review_input": artifact(input_path),
                "review_artifacts": {
                    "specialist": artifact(specialist_path),
                    "verifier": artifact(verifier_path),
                },
                "comparison_artifact": artifact(comparison_path),
                "source_snapshots": [{
                    "source_id": "SOURCE-1", "path": source_snapshot_path.name,
                    "sha256": source_snapshot_hash,
                }],
            }
            human_approval = {
                "schema_version": 1, "decision": "approve", "approver_type": "human",
                "approver_id": "test-human-reviewer", "approver_role": "qualified_agronomic_reviewer",
                "qualification_reference": "TEST ONLY; not a real credential or approval",
                "approved_at": "2026-01-03", "record_id": "CURATED-001", "review_id": review_id,
                "text_sha256": text_sha256(excerpt), "source_id": "SOURCE-1", "crop": "maize",
                "review_input_sha256": input_hash, "source_snapshot_sha256": source_snapshot_hash,
                "content_sha256": "a" * 64, "valid_from": None, "valid_until": "2099-12-31",
            }
            human_approval_path = root / "human-approval.json"
            human_approval_path.write_text(json.dumps(human_approval), encoding="utf-8")
            entry["human_approval"] = artifact(human_approval_path)
            registry_path = root / "registry.json"
            registry_path.write_text(json.dumps({"schema_version": 2, "entries": [entry]}), encoding="utf-8")
            registry = CurationRegistry(registry_path, base_dir=root)
            document = {
                "text": excerpt,
                "metadata": {
                    "curation_record_id": "CURATED-001", "source_id": "SOURCE-1",
                    "crop": "maize", "review_date": "2026-01-02",
                    "review_status": "approved",
                "approved_scope": {"crop": "maize"},
                "valid_until": "2099-12-31",
                },
            }
            self.assertTrue(registry.authorizes(document))
            flat_document = {"text": excerpt, **document["metadata"], "retrieval_distance": 0.25}
            self.assertTrue(registry.authorizes(flat_document))
            document["metadata"]["approved_scope"] = {"crop": "maize", "region": "SP"}
            document["metadata"]["region"] = "SP"
            self.assertFalse(registry.authorizes(document))
            document["metadata"]["approved_scope"] = {"crop": "maize"}
            document["metadata"].pop("region")
            document["metadata"].pop("valid_until")
            self.assertFalse(registry.authorizes(document))
            document["metadata"]["valid_until"] = "2099-12-31"
            self.assertTrue(registry.authorizes(document))
            document["metadata"]["valid_until"] = "2100-12-31"
            self.assertFalse(registry.authorizes(document))
            document["metadata"]["valid_until"] = "2099-12-31"
            expired_entry = dict(registry.entries["CURATED-001"])
            expired_entry["_validated_validity"] = {"valid_from": None, "valid_until": "2026-01-02"}
            expired_registry = CurationRegistry(entries={"CURATED-001": expired_entry})
            document["metadata"]["valid_until"] = "2026-01-02"
            self.assertFalse(expired_registry.authorizes(document))
            document["metadata"]["valid_until"] = "2099-12-31"
            document["text"] += " altered"
            self.assertFalse(registry.authorizes(document))

            # A malformed later entry must not leave an earlier approval active.
            registry_path.write_text(json.dumps({
                "schema_version": 2,
                "entries": [entry, {"record_id": "CURATED-001"}],
            }), encoding="utf-8")
            self.assertEqual(CurationRegistry(registry_path, base_dir=root).entries, {})

            registry_path.write_text(json.dumps({
                "schema_version": 2,
                "entries": [entry, entry],
            }), encoding="utf-8")
            self.assertEqual(CurationRegistry(registry_path, base_dir=root).entries, {})

            # AI agreement without a valid human sign-off must stay blocked.
            human_approval["approver_type"] = "agent"
            human_approval_path.write_text(json.dumps(human_approval), encoding="utf-8")
            entry["human_approval"] = artifact(human_approval_path)
            registry_path.write_text(json.dumps({"schema_version": 2, "entries": [entry]}), encoding="utf-8")
            self.assertEqual(CurationRegistry(registry_path, base_dir=root).entries, {})

            # Source references without the exact ingested bytes are not approval evidence.
            human_approval["approver_type"] = "human"
            human_approval_path.write_text(json.dumps(human_approval), encoding="utf-8")
            source_snapshot_path.write_text("changed after approval", encoding="utf-8")
            entry["human_approval"] = artifact(human_approval_path)
            registry_path.write_text(json.dumps({"schema_version": 2, "entries": [entry]}), encoding="utf-8")
            self.assertEqual(CurationRegistry(registry_path, base_dir=root).entries, {})

    def test_legacy_test_module_reexports_runtime_verifier(self):
        from tools.review_verifier import compare_reviews as runtime_compare_reviews
        from verify_agronomist_reviews import compare_reviews as compatibility_compare_reviews

        self.assertIs(compatibility_compare_reviews, runtime_compare_reviews)

    def test_invalid_artifact_hash_loads_as_empty_fail_closed_registry(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "registry.json"
            path.write_text(json.dumps({"schema_version": 1, "entries": [{"record_id": "x"}]}))
            self.assertEqual(CurationRegistry(path).entries, {})


if __name__ == "__main__":
    unittest.main()
