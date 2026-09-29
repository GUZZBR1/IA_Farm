import tempfile
import unittest
from pathlib import Path

from tools.dosage_calculator import DosageError, calculate_total_dose
from tools.ingest import parse_markdown_documents
from tools.memory_manager import MemoryManager
from tools.orchastrator import NO_CONTEXT_RESPONSE, Orchestrator
from run_golden_set import FixtureVectorDB
from simulation_agents import AGRONOMIST_AUDITOR


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

        response = orch.handle_request("What is the recommended dosage?", {
            "region": "Mato Grosso",
            "climate": "Tropical",
        })

        self.assertEqual(response, NO_CONTEXT_RESPONSE)

    def test_metadata_filters_are_canonicalized(self):
        db = FakeVectorDB([{
            "text": "A synthetic reference with no agronomic dose.",
            "metadata": {
                "source_id": "TEST-APPROVED-001",
                "review_status": "approved",
                "review_date": "2024-01-01",
            },
        }])
        orch = Orchestrator(db=db)

        response = orch.handle_request("What is the dosage?", {
            "region": "Mato Grosso",
            "climate": "tropical",
        })

        self.assertIn("A synthetic reference with no agronomic dose.", response)
        self.assertIn("TEST-APPROVED-001", response)
        self.assertEqual(
            db.calls[-1][1],
            {"region": "Brazil-MatoGrosso", "climate": "Tropical"},
        )

    def test_unreviewed_document_is_never_displayed(self):
        db = FakeVectorDB([{
            "text": "UNSAFE-SYNTHETIC-DOSE 999kg/ha",
            "metadata": {"source_id": "TEST-PENDING", "review_status": "pending"},
        }])
        response = Orchestrator(db=db).handle_request("Qual a dosagem?", {
            "region": "Mato Grosso",
            "climate": "Tropical",
        })
        self.assertEqual(response, NO_CONTEXT_RESPONSE)
        self.assertNotIn("999kg/ha", response)

    def test_flat_vector_index_hit_with_review_provenance_can_be_displayed(self):
        db = FakeVectorDB([{
            "text": "Reviewed flat-index reference for testing.",
            "source_id": "TEST-FLAT-APPROVED",
            "review_status": "approved",
            "review_date": "2025-01-01",
        }])

        response = Orchestrator(db=db).handle_request("Mostre a referência local.", {})

        self.assertIn("TEST-FLAT-APPROVED", response)
        self.assertIn("Reviewed flat-index reference for testing.", response)

    def test_flat_vector_index_hit_without_review_provenance_fails_closed(self):
        db = FakeVectorDB([{
            "text": "Unreviewed legacy index entry.",
            "source_id": "TEST-FLAT-UNREVIEWED",
        }])

        response = Orchestrator(db=db).handle_request("Mostre a referência local.", {})

        self.assertEqual(response, NO_CONTEXT_RESPONSE)
        self.assertNotIn("Unreviewed legacy", response)

    def test_runtime_has_no_generation_or_remote_llm_configuration(self):
        orch = Orchestrator(db=FakeVectorDB())
        self.assertFalse(hasattr(orch, "_call_llm"))
        self.assertFalse(hasattr(orch, "openrouter_api_key"))

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

    def test_simulated_retriever_enforces_region_and_climate_filters(self):
        documents = [
            {"text": "Reference for Mato Grosso.", "metadata": {
                "region": "Brazil-MatoGrosso", "climate": "Tropical",
            }},
            {"text": "Reference for Paraná.", "metadata": {
                "region": "Brazil-Parana", "climate": "Subtropical",
            }},
        ]
        results = FixtureVectorDB(documents).query(
            "planting", filters={
                "region": "Brazil-MatoGrosso", "climate": "Tropical",
            },
        )

        self.assertEqual([item["text"] for item in results], ["Reference for Mato Grosso."])

    def test_agronomist_auditor_rejects_source_from_another_region(self):
        document = {
            "text": "Paraná-specific synthetic source.",
            "metadata": {
                "source_id": "SYNTHETIC-PR",
                "review_status": "approved",
                "review_date": "2024-01-01",
                "region": "Brazil-Parana",
                "climate": "Subtropical",
            },
        }
        transcript = [{
            "user": "Oi",
            "assistant": (
                "Validated local references (shown verbatim):\n\n"
                "Source: SYNTHETIC-PR\nParaná-specific synthetic source."
            ),
            "session_state": {
                "region": "Brazil-MatoGrosso", "climate": "Tropical",
            },
            "retrieval": [],
        }]

        review = AGRONOMIST_AUDITOR.review(transcript, [document])

        self.assertFalse(review["passed"])
        self.assertTrue(any("does not match session" in item for item in review["findings"]))


if __name__ == "__main__":
    unittest.main()
