import sqlite3
import tempfile
import unittest
import copy
from pathlib import Path

from tools.knowledge_lifecycle import new_record, transition_record
from tools.knowledge_store import KnowledgeStore
from tools.knowledge_schema import json_sha256, record_sha256


class KnowledgeStoreTests(unittest.TestCase):
    def test_events_are_atomically_persisted_and_chain_verifies(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = KnowledgeStore(Path(temporary) / "knowledge.sqlite")
            record, created = new_record("fixture-1", "Synthetic fixture text", [{
                "source_id": "fixture-source", "url": "https://example.invalid/source",
                "title": "Fixture only", "publisher": "Test", "locator": "fixture",
                "accessed_at": "2026-01-01",
            }], {"topic": "test-only"}, actor_id="importer", at="2026-01-01T00:00:00+00:00")
            store.persist(record, created, expected_head=None)
            candidate, event = transition_record(record, "PARSED", actor_id="parser",
                reason="parse fixture", at="2026-01-02T00:00:00+00:00")
            store.persist(candidate, event, expected_head=record["audit_head"])
            self.assertEqual(store.get("fixture-1"), candidate)
            self.assertEqual([item["to_status"] for item in store.events("fixture-1")], ["RAW", "PARSED"])

    def test_stale_head_and_event_mutation_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = KnowledgeStore(Path(temporary) / "knowledge.sqlite")
            record, event = new_record("fixture-2", "Fixture", [{
                "source_id": "fixture-source", "url": "https://example.invalid/source",
                "title": "Fixture", "publisher": "Test", "locator": "fixture",
                "accessed_at": "2026-01-01",
            }], {"topic": "test"}, actor_id="importer", at="2026-01-01T00:00:00+00:00")
            store.persist(record, event, expected_head=None)
            with self.assertRaises(ValueError):
                store.persist(record, event, expected_head="f" * 64)
            with store._connect() as connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("DELETE FROM knowledge_audit_events")

    def test_store_rejects_forged_lifecycle_skip_even_with_recomputed_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = KnowledgeStore(Path(temporary) / "knowledge.sqlite")
            record, creation = new_record("fixture-3", "Fixture", [{
                "source_id": "fixture-source", "url": "https://example.invalid/source",
                "title": "Fixture", "publisher": "Test", "locator": "fixture",
                "accessed_at": "2026-01-01",
            }], {"topic": "test"}, actor_id="importer", at="2026-01-01T00:00:00+00:00")
            store.persist(record, creation, expected_head=None)
            parsed, event = transition_record(record, "PARSED", actor_id="parser",
                reason="parse fixture", at="2026-01-02T00:00:00+00:00")
            forged_record = copy.deepcopy(parsed)
            forged_event = copy.deepcopy(event)
            forged_record["status"] = "CANDIDATE"
            forged_event["to_status"] = "CANDIDATE"
            forged_event["after_sha256"] = record_sha256(forged_record)
            forged_event["event_sha256"] = ""
            forged_event["event_sha256"] = json_sha256({
                key: value for key, value in forged_event.items() if key != "event_sha256"})
            forged_record["audit_head"] = forged_event["event_sha256"]
            with self.assertRaises(ValueError):
                store.persist(forged_record, forged_event, expected_head=record["audit_head"])
            self.assertEqual(store.get("fixture-3")["status"], "RAW")


if __name__ == "__main__":
    unittest.main()
