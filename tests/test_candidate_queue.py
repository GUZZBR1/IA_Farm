"""The operational queue is source triage, never an agronomic approval set."""

import json
import unittest
from pathlib import Path

from tools.build_candidate_queue import build_queue

ROOT = Path(__file__).resolve().parents[1]


class CandidateQueueTests(unittest.TestCase):
    def test_all_frozen_candidates_remain_blocked_and_license_unknown(self):
        candidates = json.loads((ROOT / "tests/agronomic_gold_candidates.json").read_text(encoding="utf-8"))
        audit = json.loads((ROOT / "tests/agronomic_candidate_audit.json").read_text(encoding="utf-8"))
        queue = build_queue(candidates, audit)
        self.assertEqual(queue["counts"]["total"], 18)
        self.assertEqual(queue["counts"]["SNAPSHOT_MISSING"], 13)
        self.assertEqual(queue["counts"]["EVIDENCE_CONFLICT"], 5)
        self.assertEqual(queue["counts"]["READY_FOR_HUMAN_REVIEW"], 0)
        for candidate in queue["cases"]:
            self.assertFalse(candidate["approved"])
            self.assertIn("LICENSE_UNKNOWN", candidate["review_blockers"])
            self.assertIn("required_source", candidate)
            self.assertIn("known_locator", candidate)
            self.assertTrue(all(source["license_status"] == "UNKNOWN"
                                for source in candidate["known_sources"]))
        conflict_rows = [row for row in queue["cases"] if row["conflicts"]]
        self.assertEqual(len(conflict_rows), 5)

    def test_conflict_class_is_exact_and_not_resolved_by_ai_agreement(self):
        candidates = json.loads((ROOT / "tests/agronomic_gold_candidates.json").read_text(encoding="utf-8"))
        audit = json.loads((ROOT / "tests/agronomic_candidate_audit.json").read_text(encoding="utf-8"))
        queue = build_queue(candidates, audit)
        conflicts = {item["candidate_id"] for item in queue["cases"]
                     if item["queue"] == "EVIDENCE_CONFLICT"}
        self.assertEqual(conflicts, {
            "DRAFT-MZ-SOIL-002", "DRAFT-MZ-PEST-002", "DRAFT-MZ-PEST-005",
            "DRAFT-MZ-WATER-003", "DRAFT-MZ-STORAGE-001",
        })
        self.assertTrue(queue["reviewer_disagreement_is_not_source_conflict_proof"])

    def test_workflow_scenarios_are_safety_challenges_not_truth_labels(self):
        scenarios = json.loads((ROOT / "tests/source_review_workflow_scenarios.json").read_text(encoding="utf-8"))
        self.assertEqual(scenarios["status"], "WORKFLOW_CHALLENGES_NO_AGRONOMIC_TRUTH_LABELS")
        self.assertEqual(len(scenarios["scenarios"]), 6)
        self.assertTrue(all("forbidden_behavior" in item and "expected_workflow" in item
                            for item in scenarios["scenarios"]))


if __name__ == "__main__":
    unittest.main()
