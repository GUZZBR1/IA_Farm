"""Frozen-source acquisition artifacts stay separate from approval and truth."""

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceEvidenceArtifactTests(unittest.TestCase):
    def load(self, relative):
        return json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_source_manifests_bind_urls_bytes_and_license_evidence(self):
        manifest_paths = sorted((ROOT / "data/source_registry").glob("*/*.json"))
        self.assertEqual(len(manifest_paths), 13)
        for path in manifest_paths:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertRegex(manifest["content_hash"], r"^[0-9a-f]{64}$")
            self.assertRegex(manifest["final_url"], r"^https://")
            self.assertGreater(manifest["file_size"], 0)
            self.assertTrue(Path(manifest["filename"]).name == manifest["filename"])
            self.assertTrue(manifest["acquisition_method"])
            self.assertIn(manifest["license_status"], {
                "UNKNOWN", "LINK_ONLY", "REDISTRIBUTION_ALLOWED",
                "ATTRIBUTION_REQUIRED", "RESTRICTED", "PUBLIC_DOMAIN",
            })

    def test_candidate_queue_and_package_index_do_not_promote_knowledge(self):
        queue = self.load("tests/agronomic_candidate_queue.json")
        index = self.load("data/human_review_package_index.json")
        report = self.load("data/source_discovery_report.json")
        self.assertEqual(queue["counts"]["total"], 18)
        self.assertEqual(queue["counts"]["READY_FOR_HUMAN_REVIEW"], 11)
        self.assertEqual(queue["counts"]["APPROVED"], 0)
        self.assertEqual(queue["counts"]["PUBLISHED"], 0)
        self.assertEqual(index["ready_count"], 11)
        self.assertEqual(index["approved_count"], 0)
        self.assertEqual(len(report["records"]), 18)
        self.assertTrue(all(row["approved"] is False for row in report["records"]))
        self.assertTrue(all(package["human_decision"] is None for package in index["packages"]))

    def test_packages_bind_each_candidate_to_the_frozen_source_snapshot(self):
        index = self.load("data/human_review_package_index.json")
        source_hashes = {
            (manifest["source_id"], manifest["content_hash"])
            for path in (ROOT / "data/source_registry").glob("*/*.json")
            if (manifest := json.loads(path.read_text(encoding="utf-8")))
        }
        for package in index["packages"]:
            package_path = ROOT / package["package_json"]
            self.assertIn("local_only_reason", package)
            if not package_path.is_file():
                continue
            manifest = json.loads(package_path.read_text(encoding="utf-8"))
            self.assertTrue(manifest["decision_is_suggestion_only"])
            self.assertIsNone(manifest["human_decision"])
            self.assertEqual(manifest["snapshot_hash"], package["snapshot_hash"])
            self.assertEqual(manifest["source_metadata"]["content_hash"], package["snapshot_hash"])
            self.assertEqual(manifest["locator"]["snapshot_id"], manifest["source_metadata"]["snapshot_id"])
            self.assertEqual(manifest["locator"]["snapshot_hash"], manifest["source_metadata"]["content_hash"])
            self.assertIn((manifest["source_metadata"]["source_id"], package["snapshot_hash"]), source_hashes)
            self.assertEqual(hashlib.sha256((ROOT / package["package_json"]).read_bytes()).hexdigest(),
                             package["package_hash"])


if __name__ == "__main__":
    unittest.main()
