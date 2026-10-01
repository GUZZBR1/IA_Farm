import json
from pathlib import Path
import unittest

from export_agronomist_review import render_packet


class AgronomistReviewExportTests(unittest.TestCase):
    def test_packet_includes_every_pending_case_and_source(self):
        path = Path(__file__).with_name("agronomic_gold_candidates.json")
        candidates = json.loads(path.read_text(encoding="utf-8"))

        packet = render_packet(candidates)

        for case in candidates["cases"]:
            self.assertIn(case["id"], packet)
            self.assertIn(case["question"], packet)
        for source in candidates["sources"]:
            self.assertIn(source["url"], packet)
        self.assertIn("não é recomendação", packet)
        self.assertIn("não há aprovação humana obrigatória", packet)
        self.assertIn("Casos dependentes", packet)

    def test_packet_refuses_a_non_draft_set(self):
        with self.assertRaisesRegex(ValueError, "draft_not_for_scoring"):
            render_packet({"status": "approved", "cases": [{"id": "x"}]})

    def test_packet_refuses_an_empty_candidate_set(self):
        with self.assertRaisesRegex(ValueError, "no cases"):
            render_packet({"status": "draft_not_for_scoring", "cases": []})


if __name__ == "__main__":
    unittest.main()
