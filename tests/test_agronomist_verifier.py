from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from verify_agronomist_reviews import compare_reviews, verify_report_file


def review(role: str, verdict: str = "correct") -> dict:
    return {
        "reviewer_role": role,
        "run_report": "test-results/frozen-simulation-report.json",
        "run_report_sha256": "a" * 64,
        "reviews": [
            {
                "review_id": "battery-001:professional",
                "verdict": verdict,
                "evidence_basis": "primary_source",
                "source_supported": True,
                "scope_correct": True,
                "critical_error": False,
                "rationale": "Claim checked against the cited official source and context.",
                "sources": [
                    {
                        "url": "https://www.gov.br/agricultura/documento",
                        "title": "Manual técnico",
                        "publisher": "Ministério da Agricultura e Pecuária",
                        "source_type": "official_regulatory",
                        "edition_or_validity": "Edição vigente consultada",
                        "accessed_at": "2026-09-29",
                        "locator": "Seção 2, página 3, tabela 1",
                        "evidence": "A passagem dá suporte à alegação claim-001.",
                        "claim_ids": ["claim-001"],
                    }
                ],
            }
        ],
    }


class AgronomistVerifierTests(unittest.TestCase):
    def test_agreement_on_official_sources_is_not_precision_or_certification(self):
        result = compare_reviews(review("maize_evidence_specialist"), review("independent_verifier"))
        self.assertEqual(result["status"], "agent_agreement_official_sources")
        self.assertFalse(result["human_approval_required"])
        self.assertFalse(result["professional_certification_claim_permitted"])
        self.assertFalse(result["precision_claim_permitted"])

    def test_disagreement_is_a_closed_blocking_result(self):
        result = compare_reviews(
            review("maize_evidence_specialist"),
            review("independent_verifier", verdict="partially_correct"),
        )
        self.assertEqual(result["status"], "contested_or_insufficient_evidence")
        self.assertEqual(len(result["disagreements"]), 1)

    def test_independently_selected_locators_are_reported_without_false_verdict_conflict(self):
        master = review("maize_evidence_specialist")
        verifier = review("independent_verifier")
        verifier["reviews"][0]["sources"][0]["locator"] = "Tabela 9, página 99"
        result = compare_reviews(master, verifier)
        self.assertEqual(result["status"], "agent_agreement_official_sources")
        self.assertEqual(result["disagreements"], [])
        self.assertEqual(len(result["source_variations"]), 1)
        self.assertFalse(result["precision_claim_permitted"])

    def test_reports_must_cover_identical_frozen_run(self):
        verifier = review("independent_verifier")
        verifier["run_report"] = "other-run.json"
        with self.assertRaisesRegex(ValueError, "same run_report"):
            compare_reviews(review("maize_evidence_specialist"), verifier)

        verifier = review("independent_verifier")
        verifier["run_report_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "same run_report_sha256"):
            compare_reviews(review("maize_evidence_specialist"), verifier)

    def test_hash_is_required_and_well_formed(self):
        master = review("maize_evidence_specialist")
        master["run_report_sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            compare_reviews(master, review("independent_verifier"))

    def test_cli_report_hash_must_match_frozen_file(self):
        contents = b'{"run": "frozen"}\n'
        with tempfile.TemporaryDirectory() as directory:
            report_file = Path(directory) / "run.json"
            report_file.write_bytes(contents)
            artifact = {
                "run_report": "run.json",
                "run_report_sha256": hashlib.sha256(contents).hexdigest(),
            }
            verify_report_file(artifact, Path(directory))
            artifact["run_report_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "does not match"):
                verify_report_file(artifact, Path(directory))

    def test_reports_must_cover_exact_same_reviews(self):
        verifier = review("independent_verifier")
        verifier["reviews"] = []
        with self.assertRaisesRegex(ValueError, "non-empty array"):
            compare_reviews(review("maize_evidence_specialist"), verifier)

    def test_every_source_requires_precise_locator_and_claim_link(self):
        master = review("maize_evidence_specialist")
        master["reviews"][0]["sources"][0]["locator"] = ""
        with self.assertRaisesRegex(ValueError, "requires locator"):
            compare_reviews(master, review("independent_verifier"))

    def test_non_official_https_domain_is_rejected(self):
        master = review("maize_evidence_specialist")
        master["reviews"][0]["sources"][0]["url"] = "https://gov.br.evil.example/doc"
        with self.assertRaisesRegex(ValueError, "official HTTPS"):
            compare_reviews(master, review("independent_verifier"))

    def test_source_access_date_must_be_iso(self):
        master = review("maize_evidence_specialist")
        master["reviews"][0]["sources"][0]["accessed_at"] = "yesterday"
        with self.assertRaisesRegex(ValueError, "ISO date"):
            compare_reviews(master, review("independent_verifier"))

    def test_behavioral_abstention_needs_no_irrelevant_agronomy_citation(self):
        master = review("maize_evidence_specialist", verdict="appropriate_abstention")
        verifier = review("independent_verifier", verdict="appropriate_abstention")
        for report in (master, verifier):
            report["reviews"][0]["evidence_basis"] = "behavioral_contract"
            report["reviews"][0]["source_supported"] = False
            report["reviews"][0]["sources"] = []
        result = compare_reviews(master, verifier)
        self.assertEqual(result["status"], "behavioral_only")


if __name__ == "__main__":
    unittest.main()
