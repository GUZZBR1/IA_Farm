"""Build a disposable retrieval index from a non-empty published release only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.knowledge_release import build_manifest, load_records
from tools.vector_db import LocalVectorDB


def _retrieval_document(record: dict, curation: dict, release_id: str) -> dict:
    """Project one exact published excerpt into runtime-compatible metadata."""
    metadata = {
        "knowledge_record_id": record["record_id"],
        "curation_record_id": record["record_id"],
        "knowledge_release_id": release_id,
        **record["scope"],
        "source_id": record["sources"][0]["source_id"],
        "knowledge_status": "PUBLISHED",
        "review_status": "approved",
        "review_date": record["approval"]["reviewed_at"],
        "reviewed_at": record["approval"]["reviewed_at"],
        "review_input_sha256": curation["review_input"]["sha256"],
    }
    return {"text": record["text"], "metadata": metadata}


def build(store: Path, output: Path, model: str = "all-MiniLM-L6-v2",
          registry: Path | None = None) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing retrieval index: {output}")
    records = load_records(store)
    manifest = build_manifest(records, index_version="faiss-flatl2-v1",
                              registry_path=registry) if registry else build_manifest(
                                  records, index_version="faiss-flatl2-v1")
    registry_path = registry or (Path(__file__).resolve().parents[1] /
                                 "data" / "curation_registry.json")
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    curation_by_id = {entry["record_id"]: entry for entry in registry_payload["entries"]}
    documents = [_retrieval_document(record, curation_by_id[record["record_id"]],
                                     manifest["knowledge_release_id"]) for record in records]
    output.mkdir(parents=True)
    try:
        database = LocalVectorDB(index_path=str(output), model_name=model)
        database.index_documents(documents, exact_documents=True)
        (output / "release_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception:
        # Only remove our newly created empty/build output if the build failed.
        import shutil
        shutil.rmtree(output, ignore_errors=True)
        raise
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="all-MiniLM-L6-v2")
    parser.add_argument("--registry", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.store, args.output, args.model, args.registry), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
