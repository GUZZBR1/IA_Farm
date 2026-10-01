# Retrieval evaluation

## Status

The lexical baseline and evaluation harness are implemented with the Python standard library. The checked-in synthetic suite tests token overlap, accent normalization, metadata filters, wrong-region abstention and no-result behavior; it contains no agronomic ground truth. Results are mechanics-only. The approved suite and canonical knowledge store are empty, so there is no agronomic retrieval score.

The real vector backend uses `LocalVectorDB` + FAISS + Sentence-Transformers and reports actual dependency imports/versions. It must not fall back to mocks. In this environment, NumPy/FAISS/Sentence-Transformers availability must be probed at execution; the expected result without them is `unavailable` / `BLOCKED_BY_ENVIRONMENT`. A semantic model or source corpus is not replaced by a fixture.

## Reproduction

```sh
python -m tools.retrieval_evaluation --suite synthetic --backend lexical
python -m tools.retrieval_evaluation --suite synthetic --backend vector --model /path/to/local/model
python -m tools.retrieval_evaluation --suite approved --backend lexical
```

Each report binds dataset and corpus hashes, environment, configuration, per-query IDs, returned records and scores/distances, precision/recall/MRR, no-result/abstention behavior, wrong-region/filter mismatches, forbidden-source hits and latency. `wrong_region_rate` counts only returned hits from queries with an explicit region filter and divides mismatched-region hits by that returned-hit count; it is null when no such hits exist. Query labels are explicit. Synthetic labels measure only the fixture strings.

## Recorded experiment

On the checked-in three-record / five-query synthetic fixture (dataset SHA-256 `8dc3763bea85bb3ccfef8d416eac6d37110dff810615aa3631353684b4d5dcfa`), BM25 produced mean Recall@K `1.00`, Precision@K `0.667`, MRR `1.00`, no-result accuracy `1.00`, wrong-region rate `0.00`, and forbidden-source rate `0.00`. This tiny test fixture is not representative of maize queries or production retrieval. The precision below 1 reflects additional lexical matches; no threshold is inferred from five fixtures. The observed mean latency was about `0.14 ms` in WSL and is not a device or field benchmark.

The current vector dependency probe on WSL Python 3.12.3 found NumPy `1.26.4`, while FAISS and Sentence-Transformers imports failed (`ModuleNotFoundError`). Vector metrics are therefore unavailable (`BLOCKED_BY_ENVIRONMENT`). No packages were installed and no mock vector result was substituted. The approved query suite reports `blocked_by_no_approved_corpus` with metrics null.

The lexical method is BM25 (k1=1.5, b=0.75), Unicode accent folding and whole-token matching; metadata is filtered before ranking. No stemming, synonyms or learned parameters are used. Vector evaluation constructs a temporary index from the selected corpus; it never modifies the current runtime index. The canonical store, not FAISS metadata, defines published records.

The runtime vector query previously searched only `min(k*10, ntotal)` and filtered afterward. It now expands the candidate window until it has `k` matching records or searches the full index, and returns the FAISS distance on each hit. A regression fixture verifies a matching record beyond the old window. Published indexing copies the runtime authorization/context metadata and retains each exact approved excerpt as one index unit; it does not split the reviewed text into chunks whose hashes would fail the approval gate. This demonstrates filter-window and contract correctness only, not semantic relevance. No arbitrary score threshold or neural reranker is introduced. Threshold selection and lexical/vector/hybrid comparison require real labeled queries and records.
