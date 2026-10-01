import unittest
import tempfile
from pathlib import Path

from tools.build_knowledge_index import _retrieval_document
from tools.orchastrator import Orchestrator


class PublishedIndexProjectionTests(unittest.TestCase):
    def test_projection_preserves_approved_excerpt_and_runtime_gate_metadata(self):
        record = {
            "record_id": "synthetic-record", "text": "Synthetic fixture only.",
            "scope": {"crop": "maize", "region": "Brazil-MatoGrosso", "climate": "Tropical"},
            "sources": [{"source_id": "synthetic-source", "valid_until": "2099-12-31"}],
            "approval": {"reviewed_at": "2026-01-01"},
        }
        curation = {"review_input": {"sha256": "f" * 64}}
        document = _retrieval_document(record, curation, "test-release")
        metadata = document["metadata"]
        self.assertEqual(document["text"], record["text"])
        self.assertTrue(Orchestrator._has_review_metadata(document))
        self.assertEqual(metadata["curation_record_id"], record["record_id"])
        self.assertEqual(metadata["climate"], "Tropical")
        self.assertEqual(metadata["region"], "Brazil-MatoGrosso")
        self.assertEqual(metadata["approved_scope"], record["scope"])
        self.assertEqual(metadata["valid_until"], "2099-12-31")

    def test_exact_published_excerpts_are_not_split_into_unapproved_chunks(self):
        from tools.vector_db import LocalVectorDB

        class Array(list):
            def astype(self, _):
                return self

        class FakeIndex:
            def __init__(self, dimension):
                self.d = dimension
                self.ntotal = 0

            def add(self, rows):
                self.ntotal += len(rows)

        class FakeFaiss:
            @staticmethod
            def IndexFlatL2(dimension):
                return FakeIndex(dimension)

            @staticmethod
            def write_index(_index, _path):
                return None

        class FakeNumpy:
            @staticmethod
            def array(rows):
                return Array(rows)

        class FakeModel:
            @staticmethod
            def encode(texts):
                return Array(texts)

        def database(path):
            value = LocalVectorDB.__new__(LocalVectorDB)
            value.dimension = 8
            value.model = FakeModel()
            value._faiss = FakeFaiss()
            value._np = FakeNumpy()
            value.index = None
            value.metadata = []
            value.index_path = str(path)
            value.index_file = str(path / "faiss.index")
            value.metadata_file = str(path / "metadata.json")
            return value

        long_text = "x" * 600
        with tempfile.TemporaryDirectory() as directory:
            exact = database(Path(directory) / "exact")
            Path(exact.index_path).mkdir()
            exact.index_documents([{"text": long_text}], exact_documents=True)
            self.assertEqual(exact.index.ntotal, 1)
            self.assertEqual(exact.metadata[0]["text"], long_text)
            chunked = database(Path(directory) / "chunked")
            Path(chunked.index_path).mkdir()
            chunked.index_documents([{"text": long_text}])
            self.assertEqual(chunked.index.ntotal, 2)


if __name__ == "__main__":
    unittest.main()
