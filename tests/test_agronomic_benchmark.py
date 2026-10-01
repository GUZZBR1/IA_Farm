import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agronomic_benchmark import evaluate, main as benchmark_main
from run_agronomic_gold import run_cases


class AgronomicBenchmarkTests(unittest.TestCase):
    def test_source_research_candidates_remain_outside_the_scored_gold_set(self):
        path = Path(__file__).with_name("agronomic_gold_candidates.json")
        candidates = json.loads(path.read_text(encoding="utf-8"))
        registered_sources = {source["id"] for source in candidates["sources"]}

        self.assertEqual(candidates["status"], "draft_not_for_scoring")
        self.assertTrue(candidates["cases"])
        for case in candidates["cases"]:
            with self.subTest(case=case["id"]):
                self.assertNotEqual(case["approval_status"], "approved")
                self.assertTrue(set(case["source_ids"]) <= registered_sources)

    def test_app_run_captures_transcript_without_copying_expected_claims(self):
        class FakeOrchestrator:
            def handle_request(self, question, state):
                state["checked"] = True
                return "local app response"

        case = self.approved_case("run-case", True)
        output = run_cases(FakeOrchestrator(), [case])[0]

        self.assertEqual(output["response"], "local app response")
        self.assertTrue(output["final_session_state"]["checked"])
        self.assertNotIn("expected_claims", output)

    @staticmethod
    def approved_case(case_id, answerable):
        return {
            "id": case_id,
            "independence_group": f"independent-{case_id}",
            "question": "Test maize question?",
            "context": {"crop": "maize", "region": "Brazil-MatoGrosso", "climate": "Tropical"},
            "answerable": answerable,
            "expected_claims": ["A source-backed test claim."] if answerable else [],
            "source_ids": ["SOURCE-1"],
            "claim_evidence": ([{
                "claim": "A source-backed test claim.",
                "source_id": "SOURCE-1",
                "locator": "Seção 1, p. 2",
                "evidence": "A fonte primária sustenta a alegação.",
                "relation": "supports",
            }] if answerable else []),
            "approval_status": "approved",
            "review_record": {
                "reviewer_roles": ["maize_evidence_specialist", "independent_verifier"],
                "review_artifacts": ["master.json", "verifier.json"],
                "run_report_sha256": "a" * 64,
                "reviewed_at": "2026-09-01",
                "human_agronomist_reviewed": False,
            },
        }

    @classmethod
    def approved_gold(cls, cases):
        return {
            "minimum_answer_precision": 0.95,
            "minimum_answer_coverage": 0.5,
            "sources": [{
                "id": "SOURCE-1",
                "url": "https://www.gov.br/agricultura/documento",
                "publisher": "Primary institution",
                "title": "Reference source",
                "retrieved_at": "2026-09-01",
                "primary_source": True,
            }],
            "cases": cases,
        }

    def test_empty_gold_set_is_not_reported_as_accuracy(self):
        result = evaluate({"cases": []}, [])

        self.assertEqual(result["status"], "not_evaluable")
        self.assertIsNone(result.get("answer_precision"))

    def test_accuracy_requires_precision_coverage_and_zero_critical_errors(self):
        answerable_cases = [
            self.approved_case(f"answerable-{index}", True)
            for index in range(59)
        ]
        gold = self.approved_gold(
            answerable_cases + [self.approved_case("unanswerable", False)]
        )
        reviews = [{
            "case_id": f"answerable-{index}",
            "response_type": "answer",
            "factually_correct": True,
            "source_supported": True,
            "scope_correct": True,
            "critical_error": False,
        } for index in range(59)]
        reviews.append({
            "case_id": "unanswerable",
            "response_type": "abstain",
            "abstention_correct": True,
        })

        result = evaluate(gold, reviews)

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["answer_precision"], 1.0)
        self.assertEqual(result["answer_coverage"], 1.0)
        self.assertGreaterEqual(result["answer_precision_lower_95_ci"], 0.95)

    def test_small_perfect_sample_does_not_prove_95_percent_precision(self):
        cases = [self.approved_case(f"case-{index}", True) for index in range(58)]
        reviews = [{
            "case_id": f"case-{index}",
            "response_type": "answer",
            "factually_correct": True,
            "source_supported": True,
            "scope_correct": True,
            "critical_error": False,
        } for index in range(58)]

        result = evaluate(self.approved_gold(cases), reviews)

        self.assertEqual(result["answer_precision"], 1.0)
        self.assertLess(result["answer_precision_lower_95_ci"], 0.95)
        self.assertEqual(result["status"], "failed")

    def test_critical_error_fails_even_when_precision_is_high(self):
        gold = self.approved_gold([self.approved_case("dose", True)])
        review = [{
            "case_id": "dose",
            "response_type": "answer",
            "factually_correct": True,
            "source_supported": True,
            "scope_correct": True,
            "critical_error": True,
        }]

        result = evaluate(gold, review)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["critical_errors"], 1)

    def test_pending_case_cannot_produce_a_precision_score(self):
        case = self.approved_case("draft", True)
        case["approval_status"] = "pending_agronomist_review"

        result = evaluate(self.approved_gold([case]), [])

        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("lacks two independent AI evidence reviews", result["reason"])

    def test_case_cannot_be_promoted_without_claim_level_source_locator(self):
        case = self.approved_case("claim-evidence", True)
        case["claim_evidence"] = []

        result = evaluate(self.approved_gold([case]), [])

        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("lacks source evidence for every expected claim", result["reason"])

    def test_gold_review_record_requires_two_ai_agents_and_no_implied_human_validator(self):
        case = self.approved_case("review-record", True)
        case["review_record"]["reviewer_roles"] = ["maize_evidence_specialist"]

        result = evaluate(self.approved_gold([case]), [])

        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("requires both independent AI reviewer roles", result["reason"])

    def test_missing_run_reviews_returns_not_evaluable_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            gold_path = Path(directory) / "gold.json"
            missing_reviews = Path(directory) / "missing-reviews.json"
            gold_path.write_text(
                json.dumps(self.approved_gold([self.approved_case("case-1", True)])),
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch("sys.argv", ["agronomic_benchmark.py", str(gold_path), str(missing_reviews)]):
                with contextlib.redirect_stdout(output):
                    exit_code = benchmark_main()

        self.assertEqual(exit_code, 2)
        self.assertIn('"status": "not_evaluable"', output.getvalue())
        self.assertIn("review results file does not exist", output.getvalue())

    def test_related_prompt_variants_cannot_inflate_sample_size(self):
        first = self.approved_case("variant-a", True)
        second = self.approved_case("variant-b", True)
        second["independence_group"] = first["independence_group"]

        result = evaluate(self.approved_gold([first, second]), [])

        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("distinct independence_group", result["reason"])

    def test_gold_case_without_independence_group_is_not_evaluable(self):
        case = self.approved_case("missing-family", True)
        del case["independence_group"]

        result = evaluate(self.approved_gold([case]), [])

        self.assertEqual(result["status"], "not_evaluable")
        self.assertIn("requires a reviewer-assigned independence_group", result["reason"])


if __name__ == "__main__":
    unittest.main()
