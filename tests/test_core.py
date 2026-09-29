import tempfile
import unittest
from pathlib import Path

from tools.dosage_calculator import DosageError, calculate_total_dose
from tools.ingest import parse_markdown_documents
from tools.memory_manager import MemoryManager
from tools.orchastrator import NO_CONTEXT_RESPONSE, Orchestrator


class FakeVectorDB:
    def __init__(self, documents=None):
        self.documents = documents or []
        self.calls = []

    def query(self, query, filters=None):
        self.calls.append((query, filters))
        return self.documents


class CoreBehaviorTests(unittest.TestCase):
    def test_missing_context_is_requested_for_technical_query(self):
        db = FakeVectorDB()
        orch = Orchestrator(db=db)

        response = orch.handle_request("Quanto de NPK devo aplicar?", {})

        self.assertIn("region", response)
        self.assertIn("climate", response)
        self.assertEqual(db.calls, [])

    def test_empty_retrieval_fails_closed(self):
        orch = Orchestrator(db=FakeVectorDB())
        orch._call_llm = lambda prompt: self.fail("LLM must not run without retrieved context")

        response = orch.handle_request("What is the recommended dosage?", {
            "region": "Mato Grosso",
            "climate": "Tropical",
        })

        self.assertEqual(response, NO_CONTEXT_RESPONSE)

    def test_metadata_filters_are_canonicalized(self):
        db = FakeVectorDB([{"text": "validated context"}])
        orch = Orchestrator(db=db)
        orch._call_llm = lambda prompt: "answer"

        response = orch.handle_request("What is the dosage?", {
            "region": "Mato Grosso",
            "climate": "tropical",
        })

        self.assertEqual(response, "answer")
        self.assertEqual(
            db.calls[-1][1],
            {"region": "Brazil-MatoGrosso", "climate": "Tropical"},
        )

    def test_dosage_calculation_is_deterministic(self):
        self.assertEqual(calculate_total_dose("120kg/ha", "2.5"), "300 kg")
        with self.assertRaises(DosageError):
            calculate_total_dose("120kg", "2")

    def test_markdown_ingestion_preserves_source_and_metadata(self):
        markdown = """### Nitrogen\n- **Metadata:** {\"region\": \"General\"}\n\nDose: 120kg/ha.\n"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "dataset.md"
            source.write_text(markdown, encoding="utf-8")

            documents = parse_markdown_documents(source)

        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["metadata"]["region"], "General")
        self.assertIn("120kg/ha", documents[0]["text"])
        self.assertTrue(documents[0]["metadata"]["source"].endswith("dataset.md"))

    def test_memory_manager_persists_profile_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "memory.db"
            memory = MemoryManager(str(database))
            memory.save_profile_fact("region", "Brazil-MatoGrosso", "location")
            memory.add_interaction("question", "answer", {"region": "Brazil-MatoGrosso"})

            self.assertEqual(memory.get_profile_fact("region"), "Brazil-MatoGrosso")
            self.assertIn("question", memory.get_recent_history())


if __name__ == "__main__":
    unittest.main()
