import json
import tempfile
import unittest
from pathlib import Path

from tools.mining_agent import mine_knowledge


class CandidateIngestionTests(unittest.TestCase):
    def test_parser_emits_non_publishable_candidate_artifact_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "fixture.md"
            source.write_text("# Fixture\n\n### Generic section\nSynthetic test text only.\n",
                              encoding="utf-8")
            output = root / "candidate.json"
            count = mine_knowledge([source], str(output))
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(count, 1)
            self.assertEqual(payload["status"], "CANDIDATE")
            self.assertFalse(payload["promotion_allowed"])
            self.assertEqual(payload["records"][0]["metadata"]["review_status"], "pending")
            self.assertFalse((root / "faiss.index").exists())


if __name__ == "__main__":
    unittest.main()
