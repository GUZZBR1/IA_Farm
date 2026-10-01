"""Build a disposable retrieval index from a non-empty published release only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.knowledge_release import build_manifest, load_records
from tools.retrieval_runtime import build_index_manifest, validate_embedding_manifest
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
        "approved_scope": record["scope"],
    }
    source = record["sources"][0]
    for field in ("valid_from", "valid_until"):
        if field in source:
            metadata[field] = source[field]
    return {"text": record["text"], "metadata": metadata}


def build(store: Path, output: Path, model: str = "all-MiniLM-L6-v2",
          registry: Path | None = None, *, model_manifest_path: Path | None = None) -> dict:
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
    if model_manifest_path is None:
        raise ValueError("an explicit embedding model manifest is required; see RETRIEVAL_RUNTIME.md")
    model_manifest = json.loads(model_manifest_path.read_text(encoding="utf-8"))
    validate_embedding_manifest(model_manifest, Path(model))
    output.mkdir(parents=True)
    try:
        database = LocalVectorDB(index_path=str(output), model_name=model,
                                 model_revision=model_manifest["revision"],
                                 expected_release_id=manifest["knowledge_release_id"],
                                 model_id=model_manifest["model_id"])
        database.index_documents(documents, exact_documents=True)
        index_manifest = build_index_manifest(
            index_path=output, index_type="faiss-flat-l2-v1",
            embedding_model=model_manifest,
            knowledge_release=manifest["knowledge_release_id"],
            record_count=len(records), dimension=database.dimension)
        (output / "index_manifest.json").write_text(
            json.dumps(index_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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
    parser.add_argument("--model-manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.store, args.output, args.model, args.registry,
                           model_manifest_path=args.model_manifest), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
