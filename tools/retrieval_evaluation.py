"""Reproducible retrieval evaluation; synthetic scores never establish agronomic accuracy.

Run: python -m tools.retrieval_evaluation --suite synthetic --backend lexical
Real vectors: add --backend vector --model /path/to/local/sentence-transformers-model
Approved corpus: --suite approved --registry data/curation_registry.json
The vector backend uses actual LocalVectorDB, FAISS, and Sentence-Transformers.
Synthetic indexing uses a temporary directory; existing indexes are never written.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import tempfile
import time
from typing import Any

from tools.lexical_baseline import LexicalBaseline, matches_filters, record_metadata
from tools.retrieval_runtime import validate_embedding_manifest

ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(__file__).with_name("retrieval_eval_dataset.json")
DEPENDENCIES = {"numpy": "numpy", "faiss": "faiss-cpu", "sentence_transformers": "sentence-transformers"}


def fingerprint(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def vector_dependencies() -> dict[str, Any]:
    """Import actual packages; installed metadata alone does not prove they work."""
    result = {}
    for module, distribution in DEPENDENCIES.items():
        try:
            importlib.import_module(module)
            result[module] = {"available": True, "version": importlib.metadata.version(distribution)}
        except Exception as exc:
            result[module] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return result


def validate_suite(suite: dict[str, Any], kind: str) -> None:
    """Runtime validation mirrors the checked-in schema without a new dependency."""
    if kind not in {"synthetic", "approved"} or not isinstance(suite, dict):
        raise ValueError("unknown retrieval evaluation suite")
    if not isinstance(suite.get("records"), list) or not isinstance(suite.get("cases"), list):
        raise ValueError("suite records and cases must be arrays")
    record_ids = set()
    for record in suite["records"]:
        if not isinstance(record, dict) or not isinstance(record.get("text"), str) or not record["text"].strip():
            raise ValueError("each record requires nonempty text")
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError("record metadata must be an object")
        record_id = metadata.get("eval_record_id")
        if not isinstance(record_id, str) or not record_id or record_id in record_ids:
            raise ValueError("evaluation record IDs must be nonempty and unique")
        record_ids.add(record_id)
    case_ids = set()
    for case in suite["cases"]:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in case_ids:
            raise ValueError("case IDs must be nonempty and unique")
        case_ids.add(case_id)
        if case.get("query_id") != case_id or not isinstance(case.get("context"), dict):
            raise ValueError("each case requires a stable query_id and context object")
        if not isinstance(case.get("query"), str) or not case["query"].strip():
            raise ValueError("case requires a nonempty query")
        if not isinstance(case.get("filters"), dict):
            raise ValueError("case filters must be an object")
        if not isinstance(case.get("expected_abstention"), bool):
            raise ValueError("expected_abstention must be boolean")
        k = case.get("k")
        if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
            raise ValueError("case k must be a positive integer")
        expected = case.get("expected_record_ids")
        if not isinstance(expected, list) or any(not isinstance(item, str) or not item for item in expected):
            raise ValueError("expected_record_ids must be an array of nonempty strings")
        if len(expected) != len(set(expected)):
            raise ValueError("expected_record_ids must be unique")
        forbidden = case.get("forbidden_record_ids", [])
        if not isinstance(forbidden, list) or any(not isinstance(item, str) or not item for item in forbidden):
            raise ValueError("forbidden_record_ids must be an array of nonempty strings")
        label = case.get("label")
        if label not in {"relevant", "abstain", "unscored"}:
            raise ValueError("unknown retrieval label")
        if (label == "relevant") != bool(expected):
            raise ValueError("only relevant cases must have expected records")
        if case["expected_abstention"] != (label == "abstain"):
            raise ValueError("expected_abstention conflicts with retrieval label")
        evidence = case.get("label_evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("case requires a label evidence description")
        if kind == "synthetic" and not (set(expected) | set(forbidden)) <= record_ids:
            raise ValueError("synthetic labels reference missing fixture IDs")


def score_case(case: dict[str, Any], hits: list[dict[str, Any]], allowed_ids: set[str]) -> dict[str, Any]:
    """Record-level recall/MRR deduplicate chunks at their first returned position.

    Precision uses unique records in the returned k chunks. Empty relevant retrieval
    has precision zero. Abstention means zero returned records and is scored only
    for explicitly grounded abstain labels. Unscored queries have null metrics.
    """
    hits = hits[:case["k"]]
    ids = [record_metadata(hit).get("eval_record_id") for hit in hits]
    if any(record_id not in allowed_ids for record_id in ids):
        raise ValueError("retriever returned unknown evaluation record IDs")
    unique_ids = list(dict.fromkeys(ids))
    mismatches = sum(not matches_filters(hit, case["filters"]) for hit in hits)
    forbidden = set(case.get("forbidden_record_ids", []))
    region = case["filters"].get("region")
    wrong_region_hits = (sum(not matches_filters(hit, {"region": region}) for hit in hits)
                         if region is not None else 0)
    result = {
        "case_id": case["id"], "query": case["query"], "filters": case["filters"],
        "k": case["k"], "label": case["label"], "label_evidence": case["label_evidence"],
        "expected_record_ids": case["expected_record_ids"], "returned_record_ids": ids,
        "returned_scores": [{
            "record_id": record_metadata(hit).get("eval_record_id"),
            "retrieval_score": hit.get("retrieval_score"),
            "retrieval_distance": hit.get("retrieval_distance"),
        } for hit in hits],
        "unique_returned_record_ids": unique_ids, "filter_mismatches": mismatches,
        "forbidden_source_hits": len(forbidden.intersection(unique_ids)),
        "wrong_region_hits": wrong_region_hits,
        "region_filtered_hit_count": len(hits) if region is not None else 0,
        "recall_at_k": None, "precision_at_k": None, "reciprocal_rank_at_k": None,
        "abstention_correct": None,
    }
    if case["label"] == "abstain":
        result["abstention_correct"] = not ids
    elif case["label"] == "relevant":
        expected = set(case["expected_record_ids"])
        relevant = expected.intersection(unique_ids)
        result["recall_at_k"] = len(relevant) / len(expected)
        result["precision_at_k"] = len(relevant) / len(unique_ids) if unique_ids else 0.0
        result["reciprocal_rank_at_k"] = next((1 / rank for rank, record_id in enumerate(ids, 1)
                                                 if record_id in expected), 0.0)
    return result


def evaluate(retriever: Any, cases: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    record_ids = {record_metadata(record)["eval_record_id"] for record in records}
    for case in cases:
        if not set(case["expected_record_ids"]) <= record_ids:
            raise ValueError("expected record is absent from the evaluated corpus")
    rows = []
    for case in cases:
        started = time.perf_counter()
        hits = retriever.query(case["query"], k=case["k"], filters=case["filters"])
        row = score_case(case, hits, record_ids)
        row["latency_ms"] = (time.perf_counter() - started) * 1000
        rows.append(row)
    relevant = [row for row in rows if row["label"] == "relevant"]
    abstentions = [row for row in rows if row["label"] == "abstain"]
    def average(field: str) -> float | None:
        return sum(row[field] for row in relevant) / len(relevant) if relevant else None
    return {
        "status": "evaluated" if relevant or abstentions else "not_evaluable",
        "case_count": len(rows), "relevant_case_count": len(relevant),
        "abstention_case_count": len(abstentions),
        "unscored_case_count": sum(row["label"] == "unscored" for row in rows),
        "metrics": {
            "mean_recall_at_k": average("recall_at_k"),
            "mean_precision_at_k": average("precision_at_k"),
            "mrr_at_k": average("reciprocal_rank_at_k"),
            "abstention_accuracy": (sum(row["abstention_correct"] for row in abstentions) / len(abstentions)
                                     if abstentions else None),
            "no_result_accuracy": (sum(row["abstention_correct"] for row in abstentions) / len(abstentions)
                                   if abstentions else None),
            "filter_mismatch_count": sum(row["filter_mismatches"] for row in rows),
            "wrong_region_rate": (
                sum(row["wrong_region_hits"] for row in rows) /
                sum(row["region_filtered_hit_count"] for row in rows)
                if sum(row["region_filtered_hit_count"] for row in rows) else None
            ),
            "forbidden_source_rate": (sum(row["forbidden_source_hits"] for row in rows) /
                                      sum(len(row["unique_returned_record_ids"]) for row in rows)
                                      if any(row["unique_returned_record_ids"] for row in rows) else 0.0),
            "mean_latency_ms": (sum(row["latency_ms"] for row in rows) / len(rows) if rows else None),
        },
        "cases": rows,
    }


def approved_records(store_path: Path, registry_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read canonical published records; never treat index metadata as authority."""
    from tools.knowledge_schema import validate_record
    from tools.knowledge_release import validate_published_authority
    payload = json.loads(store_path.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise ValueError("approved knowledge store must contain a records array")
    approved = []
    for record in records:
        validate_record(record)
        if record["status"] == "PUBLISHED":
            approved.append({"text": record["text"], "metadata": {
                "eval_record_id": record["record_id"],
                "region": record["scope"].get("region"),
                "crop": record["scope"].get("crop"),
                "source_id": record["sources"][0]["source_id"],
            }})
    if approved:
        validate_published_authority([record for record in records if record["status"] == "PUBLISHED"],
                                     registry_path)
    audit = {"knowledge_store_sha256": hashlib.sha256(store_path.read_bytes()).hexdigest(),
             "published_record_count": len(approved)}
    return approved, audit


def run(dataset: dict[str, Any], suite_name: str, backend: str, model: str,
        registry: Path, store: Path, model_manifest_path: Path | None = None) -> dict[str, Any]:
    if dataset.get("schema_version") != 1:
        raise ValueError("unsupported retrieval dataset schema")
    suite = dataset["suites"][suite_name]
    validate_suite(suite, suite_name)
    records, audit = (approved_records(store, registry) if suite_name == "approved"
                      else (suite["records"], {}))
    report = {
        "schema_version": 1, "suite": suite_name, "backend": backend,
        "score_scope": "SYNTHETIC_RETRIEVAL_EVALUATION" if suite_name == "synthetic" else "APPROVED_CORPUS_RETRIEVAL",
        "agronomic_accuracy_claim": False, "dataset_sha256": fingerprint(dataset),
        "corpus_sha256": fingerprint(records), "python": sys.version.split()[0],
        "platform": platform.platform(), "corpus_record_count": len(records), **audit,
        "configuration": {"ranking": "BM25" if backend == "lexical" else "LocalVectorDB IndexFlatL2",
                          "model": model if backend == "vector" else None,
                          "lexical_k1": 1.5 if backend == "lexical" else None,
                          "lexical_b": 0.75 if backend == "lexical" else None},
    }
    if suite_name == "approved" and not records:
        report.update(status="blocked_by_no_approved_corpus", metrics=None, cases=[])
        report["reason"] = "No PUBLISHED records in the canonical knowledge store; agronomic retrieval is unscored."
        return report
    if backend == "lexical":
        report.update(evaluate(LexicalBaseline(records), suite["cases"], records))
        report["fallback_policy"] = "LEXICAL_SELECTED_EXPLICITLY_BY_CALLER"
        return report
    dependencies = vector_dependencies()
    report["dependencies"] = dependencies
    if not all(item["available"] for item in dependencies.values()):
        report.update(status="blocked_by_environment", capability_state="DEPENDENCY_MISSING",
                      reason="Real vector dependencies failed to import.", metrics=None, cases=[])
        return report
    if not Path(model).is_dir():
        report.update(status="blocked_by_environment", capability_state="MODEL_MISSING",
                      reason="Vector evaluation requires an existing local model directory; downloads are disabled.",
                       metrics=None, cases=[])
        return report
    if model_manifest_path is None or not Path(model_manifest_path).is_file():
        report.update(status="invalid", capability_state="MODEL_MISSING",
                      reason="An explicit embedding manifest with immutable revision and artifact hash is required.",
                      metrics=None, cases=[])
        return report
    model_manifest = json.loads(Path(model_manifest_path).read_text(encoding="utf-8"))
    try:
        validate_embedding_manifest(model_manifest, Path(model))
    except ValueError as error:
        report.update(status="invalid", capability_state="MODEL_MISSING",
                      reason=str(error), metrics=None, cases=[])
        return report
    from tools.vector_db import LocalVectorDB
    try:
        with tempfile.TemporaryDirectory(prefix="ia-farm-retrieval-eval-") as directory:
            database = LocalVectorDB(index_path=directory, model_name=model,
                                     model_revision=model_manifest["revision"],
                                     model_id=model_manifest["model_id"])
            if database.dimension != model_manifest["expected_dimension"]:
                raise RuntimeError("Loaded model dimension differs from the pinned model manifest")
            database.index_documents(records)
            report["vector_count"] = database.index.ntotal
            report["vector_dimension"] = database.index.d
            report.update(evaluate(database, suite["cases"], records))
    except (RuntimeError, OSError, ImportError) as exc:
        report.update(status="blocked_by_environment", capability_state="INDEX_INVALID",
                      reason=f"{type(exc).__name__}: {exc}", metrics=None, cases=[])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--suite", choices=("synthetic", "approved"), default="synthetic")
    parser.add_argument("--backend", choices=("lexical", "vector"), default="lexical")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Exact local model path preferred for reproducibility.")
    parser.add_argument("--model-manifest", type=Path, help="Pinned revision and local model artifact hash.")
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "curation_registry.json")
    parser.add_argument("--store", type=Path, default=ROOT / "data" / "knowledge_base" / "approved_records.json")
    parser.add_argument("--output", type=Path, help="Optional JSON report; otherwise prints to stdout.")
    args = parser.parse_args()
    try:
        dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
        report = run(dataset, args.suite, args.backend, args.model, args.registry, args.store,
                     args.model_manifest)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report = {"status": "invalid", "reason": f"{type(exc).__name__}: {exc}", "metrics": None}
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    return 0 if report["status"] == "evaluated" else 2


if __name__ == "__main__":
    raise SystemExit(main())
