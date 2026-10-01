"""Exercise the real FAISS/Sentence-Transformers path without altering its index."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.orchastrator import NO_CONTEXT_RESPONSE, Orchestrator
from tools.vector_db import LocalVectorDB


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        type=Path,
        default=ROOT / "data" / "vector_index",
        help="Existing FAISS index directory; queried read-only.",
    )
    args = parser.parse_args()
    index_path = args.index.resolve()
    faiss_file = index_path / "faiss.index"
    metadata_file = index_path / "metadata.json"
    original_hashes = (_sha256(faiss_file), _sha256(metadata_file))

    database = LocalVectorDB(index_path=str(index_path))
    if database.index is None or database.index.ntotal != len(database.metadata):
        raise AssertionError("FAISS vector count and metadata count differ")
    if database.index.ntotal == 0:
        raise AssertionError("existing FAISS index is empty")

    hits = database.query(
        "Spodoptera frugiperda small holes sawdust in the whorl", k=3
    )
    if not hits:
        raise AssertionError("semantic query returned no matches")
    scope = hits[0].get("region")
    if not scope:
        raise AssertionError("top result has no region metadata for filter validation")
    scoped_hits = database.query(
        "Spodoptera frugiperda", k=5, filters={"region": scope}
    )
    if not scoped_hits or any(hit.get("region") != scope for hit in scoped_hits):
        raise AssertionError("metadata filter returned no results or leaked another scope")
    if database.query(
        "Spodoptera frugiperda", filters={"region": "no-such-region"}
    ):
        raise AssertionError("unknown metadata filter should return no results")

    response = Orchestrator(db=database).rag_query(
        "What does the local reference say about this maize pest?"
    )
    if response != NO_CONTEXT_RESPONSE:
        raise AssertionError("unapproved legacy index content bypassed the runtime curation gate")

    marker = "unique synthetic FAISS round trip 6d20a"
    with tempfile.TemporaryDirectory(prefix="ia-farm-faiss-validation-") as temp:
        write_db = LocalVectorDB(index_path=temp)
        write_db.index_documents([{
            "text": marker,
            "metadata": {"region": "Brazil-Parana", "kind": "synthetic-test"},
        }])
        added = write_db.query(
            marker,
            filters={"region": "Brazil-Parana", "kind": "synthetic-test"},
        )
        if write_db.index.ntotal != len(write_db.metadata) or len(added) != 1:
            raise AssertionError("temporary FAISS index write/read round trip failed")
        if write_db.query(marker, filters={"kind": "missing"}):
            raise AssertionError("temporary index filter did not reject non-matching metadata")

    if original_hashes != (_sha256(faiss_file), _sha256(metadata_file)):
        raise AssertionError("validation modified the existing index")
    print(
        "REAL VECTOR DB VALIDATION PASSED: "
        f"vectors={database.index.ntotal}, dimension={database.index.d}, "
        f"semantic_hits={len(hits)}, scoped_hits={len(scoped_hits)}, "
        "runtime_gate=fail-closed, temporary_write_round_trip=passed, "
        "production_index=unchanged"
    )
    print(f"Top semantic match: {hits[0].get('section')} | {hits[0].get('source')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
