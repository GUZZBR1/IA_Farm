"""Synthetic mechanics tests; no test content is agronomic evidence."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.knowledge_release import build_manifest
from tools.knowledge_schema import content_sha256
from tools.lexical_baseline import LexicalBaseline, tokenize
from tools.retrieval_evaluation import DATASET, run, validate_suite


class LexicalBaselineTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.suite = self.dataset["suites"]["synthetic"]

    def test_tokenization_ignores_accents_and_case(self):
        self.assertEqual(tokenize("ÁRVORE sem acento"), tokenize("arvore SEM acento"))

    def test_metadata_is_filtered_before_ranking_and_aliases_match(self):
        records = self.suite["records"]
        result = LexicalBaseline(records).query("blue gear", k=3, filters={"region": "SP"})
        self.assertEqual(result[0]["metadata"]["eval_record_id"], "fixture-gamma")
        self.assertTrue(all(item["metadata"]["region"] == "Brazil-SaoPaulo" for item in result))

    def test_synthetic_metrics_are_separate_and_reproducible(self):
        first = run(self.dataset, "synthetic", "lexical", "unused", Path("unused"), Path("unused"))
        second = run(self.dataset, "synthetic", "lexical", "unused", Path("unused"), Path("unused"))
        self.assertEqual(first["dataset_sha256"], second["dataset_sha256"])
        self.assertEqual({key: value for key, value in first["metrics"].items() if key != "mean_latency_ms"},
                         {key: value for key, value in second["metrics"].items() if key != "mean_latency_ms"})
        self.assertFalse(first["agronomic_accuracy_claim"])
        self.assertEqual(first["score_scope"], "SYNTHETIC_RETRIEVAL_EVALUATION")
        self.assertEqual(first["fallback_policy"], "LEXICAL_SELECTED_EXPLICITLY_BY_CALLER")
        self.assertEqual(first["metrics"]["mean_recall_at_k"], 1.0)
        self.assertEqual(first["metrics"]["wrong_region_rate"], 0.0)
        self.assertEqual(first["metrics"]["no_result_accuracy"], 1.0)

    def test_approved_suite_is_blocked_without_published_store(self):
        report = run(self.dataset, "approved", "lexical", "unused", Path("data/curation_registry.json"),
                     Path("data/knowledge_base/approved_records.json"))
        self.assertEqual(report["status"], "blocked_by_no_approved_corpus")
        self.assertIsNone(report["metrics"])

    def test_release_rejects_empty_or_unpublished_records(self):
        with self.assertRaises(ValueError):
            build_manifest([])

    def test_self_asserted_published_record_cannot_enter_release(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snapshot = root / "source.snapshot"
            snapshot.write_text("Synthetic fixture only", encoding="utf-8")
            source_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
            record = {
                "schema_version": 1, "record_id": "self-asserted", "revision": 1,
                "status": "PUBLISHED", "text": "Synthetic fixture only",
                "text_sha256": hashlib.sha256(b"Synthetic fixture only").hexdigest(),
                "sources": [{"source_id": "fixture-source", "url": "https://example.invalid/source",
                    "title": "Fixture", "publisher": "Test", "locator": "fixture", "accessed_at": "2026-01-01",
                    "snapshot_ref": "source.snapshot", "snapshot_sha256": source_hash}],
                "scope": {"crop": "fixture"}, "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-03T00:00:00+00:00", "created_by": "fixture",
                "approval": {"review_id": "fixture-case", "reviewer_ids": ["reviewer-a", "reviewer-b"],
                    "approver_id": "human-a", "approver_type": "human", "reviewed_at": "2026-01-02",
                    "approved_at": "2026-01-03T00:00:00+00:00", "content_sha256": "0" * 64,
                    "review_entry_sha256": "0" * 64}, "audit_head": "0" * 64,
            }
            record["approval"]["content_sha256"] = content_sha256(record)
            registry = root / "registry.json"
            registry.write_text(json.dumps({"schema_version": 2, "entries": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                build_manifest([record], registry_path=registry, base_dir=root)

    def test_invalid_dataset_labels_fail(self):
        malformed = json.loads(json.dumps(self.suite))
        malformed["cases"][0]["expected_record_ids"] = ["missing"]
        with self.assertRaises(ValueError):
            validate_suite(malformed, "synthetic")


class FilterExpansionTests(unittest.TestCase):
    def test_vector_query_expands_beyond_initial_k_times_ten_after_filters(self):
        from tools.vector_db import LocalVectorDB

        class Array:
            def astype(self, _):
                return self

        class Model:
            def encode(self, _):
                return Array()

        class SearchIndex:
            ntotal = 25

            def search(self, _vector, count):
                return [[float(i) for i in range(count)]], [[i for i in range(count)]]

        db = LocalVectorDB.__new__(LocalVectorDB)
        db.index = SearchIndex()
        db.model = Model()
        db.metadata = [{"record_id": f"r{i}", "region": "wrong"} for i in range(20)]
        db.metadata += [{"record_id": f"r{i}", "region": "Brazil-SaoPaulo"} for i in range(20, 25)]
        result = db.query("fixture", k=1, filters={"region": "SP"})
        self.assertEqual(result[0]["record_id"], "r20")
        self.assertEqual(result[0]["retrieval_distance"], 20.0)


if __name__ == "__main__":
    unittest.main()
