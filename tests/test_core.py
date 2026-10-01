import tempfile
import unittest
from pathlib import Path

from tools.dosage_calculator import DosageError, calculate_total_dose
from tools.ingest import parse_markdown_documents
from tools.memory_manager import MemoryManager
from tools.orchastrator import NO_CONTEXT_RESPONSE, REFERENCE_HEADER, Orchestrator
from tools.curation_registry import CurationRegistry, text_sha256
from tools.contracts import VectorRetriever
from run_golden_set import FixtureVectorDB
from simulation_agents import AGRONOMIST_AUDITOR


class FakeVectorDB:
    def __init__(self, documents=None):
        self.documents = documents or []
        self.calls = []

    def query(self, query, filters=None):
        self.calls.append((query, filters))
        return self.documents


def synthetic_registry(document):
    """Explicit test-only allowlist; never written to the production registry."""
    metadata = document.get("metadata", document)
    record_id = "TEST-" + str(metadata.get("source_id") or metadata.get("source"))
    metadata["curation_record_id"] = record_id
    metadata["approved_scope"] = {
        key: value for key, value in metadata.items()
        if key not in {"curation_record_id", "knowledge_record_id", "knowledge_release_id",
                       "source_id", "source", "knowledge_status", "review_status",
                       "review_date", "reviewed_at", "review_input_sha256",
                           "approved_scope", "valid_from", "valid_until", "text", "retrieval_distance"}
    }
    return CurationRegistry(entries={record_id: {
        "record_id": record_id,
        "approval_status": "approved",
        "text_sha256": text_sha256(str(document.get("text", "")).strip()),
        "source_id": metadata.get("source_id") or metadata.get("source"),
        "crop": metadata.get("crop"),
        "review_date": metadata.get("review_date") or metadata.get("reviewed_at"),
        "review_artifacts_verified": True,
        "source_snapshots_verified": True,
        "human_approval_verified": True,
        "review_input_sha256": "synthetic-test-only",
        "approved_scope": metadata["approved_scope"],
    }})


class CoreBehaviorTests(unittest.TestCase):
    def test_fake_retriever_implements_application_retriever_contract(self):
        self.assertIsInstance(FakeVectorDB(), VectorRetriever)

    def test_missing_context_is_requested_for_technical_query(self):
        db = FakeVectorDB()
        orch = Orchestrator(db=db)

        response = orch.handle_request("Quanto de NPK devo aplicar?", {})

        self.assertIn("região da propriedade", response)
        self.assertIn("clima local", response)
        self.assertNotIn("dosagem", response.casefold())
        self.assertEqual(db.calls, [])

    def test_existing_context_is_reused_without_reasking(self):
        db = FakeVectorDB()
        orch = Orchestrator(db=db)

        response = orch.handle_request("Quanto NPK devo aplicar?", {
            "region": "Mato Grosso",
            "climate": "Tropical",
        })

        self.assertNotIn("preciso de mais informações", response.casefold())
        self.assertEqual(
            db.calls,
            [("Quanto NPK devo aplicar?", {
                "region": "Brazil-MatoGrosso",
                "climate": "Tropical",
            })],
        )

    def test_reference_header_does_not_claim_agronomic_recommendation(self):
        db = FakeVectorDB([{
            "text": "Reference excerpt for test only.",
            "metadata": {
                "source_id": "TEST-APPROVED-002",
                "review_status": "approved",
                "review_date": "2025-01-01",
                "crop": "maize",
            },
        }])

        response = Orchestrator(
            db=db, curation_registry=synthetic_registry(db.documents[0])
        ).handle_request("Mostre a fonte.", {})

        self.assertIn(REFERENCE_HEADER, response)
        self.assertIn("não constituem recomendação", response.casefold())

    def test_inline_context_correction_uses_last_affirmative_alias(self):
        orch = Orchestrator(db=FakeVectorDB())

        metadata = orch._extract_metadata(
            "Estou em Mato Grosso, clima tropical; corrigindo, Paraná, subtropical."
        )

        self.assertEqual(
            metadata,
            {"region": "Brazil-Parana", "climate": "Subtropical"},
        )

    def test_ambiguous_region_clears_stale_context_and_requests_clarification(self):
        db = FakeVectorDB()
        orch = Orchestrator(db=db)
        state = {"region": "Brazil-Bahia", "climate": "Tropical"}

        response = orch.handle_request("Estou em SP ou MT; qual dose de adubo?", state)

        self.assertIn("região da propriedade", response)
        self.assertEqual(state["region"], "")
        self.assertEqual(db.calls, [])

    def test_explicit_correction_resolves_an_earlier_either_or(self):
        orch = Orchestrator(db=FakeVectorDB())

        metadata = orch._extract_metadata(
            "Estou em SP ou MT; na verdade, agora estou no MT, clima semi árido."
        )

        self.assertEqual(metadata["region"], "Brazil-MatoGrosso")
        self.assertEqual(metadata["climate"], "Semi-arid")

    def test_negation_with_more_clears_region_instead_of_reusing_it(self):
        metadata = Orchestrator(db=FakeVectorDB())._extract_metadata(
            "Não estou mais em Mato Grosso."
        )

        self.assertEqual(metadata, {"region": ""})

    def test_ambiguous_region_still_extracts_explicit_climate(self):
        metadata = Orchestrator(db=FakeVectorDB())._extract_metadata(
            "Estou em SP ou MT, com clima semiárido."
        )

        self.assertEqual(metadata, {"region": "", "climate": "Semi-arid"})

    def test_common_agronomy_terms_are_treated_as_technical(self):
        for question in (
            "Qual adubação recomendada para milho?",
            "Que manejo devo usar para a lagarta-do-cartucho?",
            "Quais sintomas devo observar no milho?",
            "Que manejo devo adotar para plantas daninhas?",
            "Minhas folhas estão amarelas.",
            "O milho está roxo.",
        ):
            with self.subTest(question=question):
                self.assertTrue(Orchestrator._is_technical_request(question))

    def test_reference_lookup_applies_known_scope_and_blocks_other_region(self):
        db = FakeVectorDB([{
            "text": "Paraná-specific source excerpt.",
            "metadata": {
                "source_id": "TEST-PR",
                "review_status": "approved",
                "review_date": "2025-01-01",
                "crop": "maize",
                "region": "Brazil-Parana",
                "climate": "Subtropical",
            },
        }])
        state = {"region": "Mato Grosso", "climate": "Tropical"}

        response = Orchestrator(db=db).handle_request(
            "Mostre a referência local.", state
        )

        self.assertEqual(response, NO_CONTEXT_RESPONSE)
        self.assertEqual(db.calls[-1][1], {
            "region": "Brazil-MatoGrosso", "climate": "Tropical",
        })

    def test_region_scoped_reference_is_not_shown_without_region_context(self):
        document = {
            "text": "Region-specific reference excerpt.",
            "source_id": "TEST-SCOPED",
            "review_status": "approved",
            "review_date": "2025-01-01",
            "crop": "maize",
            "region": "Brazil-Parana",
            "climate": "Subtropical",
        }

        response = Orchestrator(db=FakeVectorDB([document])).handle_request(
            "Mostre uma referência local.", {}
        )

        self.assertEqual(response, NO_CONTEXT_RESPONSE)
        self.assertNotIn("Region-specific", response)

    def test_auditor_independently_flags_missed_agronomy_intent(self):
        user_input = "Qual adubação recomendada para milho?"
        self.assertTrue(AGRONOMIST_AUDITOR._expects_context(user_input))

        review = AGRONOMIST_AUDITOR.review([{
            "user": user_input,
            "assistant": "Generic advice without context.",
            "session_state": {},
            "retrieval": [],
        }], [])

        self.assertFalse(review["passed"])
        self.assertTrue(any("missing context was not requested" in item for item in review["findings"]))

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
                "crop": "maize",
            },
        }])
        orch = Orchestrator(
            db=db, curation_registry=synthetic_registry(db.documents[0])
        )

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

    def test_approved_metadata_without_registry_entry_fails_closed(self):
        document = {
            "text": "Metadata alone is not authorization.",
            "metadata": {
                "source_id": "FORGED-APPROVAL", "review_status": "approved",
                "review_date": "2025-01-01", "crop": "maize",
            },
        }
        response = Orchestrator(db=FakeVectorDB([document])).handle_request(
            "Mostre a referência local.", {}
        )
        self.assertEqual(response, NO_CONTEXT_RESPONSE)

    def test_registry_hash_mismatch_fails_closed(self):
        document = {
            "text": "Reviewed text, then modified.",
            "metadata": {
                "source_id": "TEST-HASH", "review_status": "approved",
                "review_date": "2025-01-01", "crop": "maize",
            },
        }
        registry = synthetic_registry(document)
        document["text"] += " changed"
        response = Orchestrator(
            db=FakeVectorDB([document]), curation_registry=registry
        ).handle_request("Mostre a referência local.", {})
        self.assertEqual(response, NO_CONTEXT_RESPONSE)

    def test_flat_vector_index_hit_with_review_provenance_can_be_displayed(self):
        document = {
            "text": "Reviewed flat-index reference for testing.",
            "source_id": "TEST-FLAT-APPROVED",
            "review_status": "approved",
            "review_date": "2025-01-01",
            "crop": "maize",
        }
        db = FakeVectorDB([document])

        response = Orchestrator(
            db=db, curation_registry=synthetic_registry(document)
        ).handle_request("Mostre a referência local.", {})

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

    def test_ingestion_cannot_self_approve_or_forge_source_provenance(self):
        markdown = (
            '### Alegação\n- **Metadata:** '
            '{"source":"https://fake.example/official.pdf", '
            '"source_id":"FAKE-APPROVAL", "review_status":"approved", '
            '"review_date":"2026-01-01", "reviewer":"Agronomist", '
            '"crop":"maize", "region":"Brazil-MatoGrosso", '
            '"climate":"Tropical"}\n\nConteúdo não revisado.\n'
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "untrusted.md"
            source.write_text(markdown, encoding="utf-8")

            document = parse_markdown_documents(source)[0]

        metadata = document["metadata"]
        self.assertEqual(metadata["source"], str(source))
        self.assertEqual(metadata["review_status"], "pending")
        self.assertNotIn("source_id", metadata)
        self.assertNotIn("reviewer", metadata)
        self.assertFalse(Orchestrator(db=FakeVectorDB())._is_reviewed(document))

        response = Orchestrator(db=FakeVectorDB([document])).handle_request(
            "Mostre a fonte local.", {}
        )
        self.assertEqual(response, NO_CONTEXT_RESPONSE)
        self.assertNotIn("Conteúdo não revisado", response)

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
                "crop": "maize",
                "region": "Brazil-Parana",
                "climate": "Subtropical",
            },
        }
        transcript = [{
            "user": "Oi",
            "assistant": (
                f"{REFERENCE_HEADER}\n\n"
                "Fonte: SYNTHETIC-PR\nParaná-specific synthetic source."
            ),
            "session_state": {
                "region": "Brazil-MatoGrosso", "climate": "Tropical",
            },
            "retrieval": [],
        }]

        review = AGRONOMIST_AUDITOR.review(transcript, [document])

        self.assertFalse(review["passed"])
        self.assertTrue(any("does not match session" in item for item in review["findings"]))

    def test_agronomist_auditor_accepts_flat_real_index_metadata_shape(self):
        document = {
            "text": "A source excerpt with no agronomic recommendation.",
            "source_id": "TEST-FLAT-AUDIT",
            "review_status": "approved",
            "review_date": "2025-01-01",
            "crop": "maize",
        }
        transcript = [{
            "user": "Mostre uma referência local.",
            "assistant": (
                f"{REFERENCE_HEADER}\n\n"
                "Fonte: TEST-FLAT-AUDIT\n"
                "A source excerpt with no agronomic recommendation."
            ),
            "session_state": {},
            "retrieval": [],
        }]

        review = AGRONOMIST_AUDITOR.review(transcript, [document])

        self.assertTrue(review["passed"], review["findings"])

    def test_reviewed_source_for_another_crop_is_never_displayed(self):
        document = {
            "text": "Synthetic soybean-only reference.",
            "metadata": {
                "source_id": "SYNTHETIC-SOY",
                "review_status": "approved",
                "review_date": "2024-01-01",
                "crop": "soybean",
            },
        }

        response = Orchestrator(db=FakeVectorDB([document])).handle_request(
            "Mostre a referência local.", {}
        )

        self.assertEqual(response, NO_CONTEXT_RESPONSE)
        self.assertNotIn("soybean-only", response)


if __name__ == "__main__":
    unittest.main()
