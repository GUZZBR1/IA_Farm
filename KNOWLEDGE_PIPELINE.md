# Knowledge pipeline

Status: **DESIGN + structural implementation**. No agronomic record is approved or published. The machine-readable record contract is [`schemas/knowledge_record.schema.json`](schemas/knowledge_record.schema.json); Python validation and transition rules live in `tools/knowledge_schema.py` and `tools/knowledge_lifecycle.py`.

## Trust boundaries

```text
raw source snapshot → parse → candidate → review → human approval → published store → manifest → disposable index
```

`tools/ingest.py` and `tools/mining_agent.py` parse local Markdown into candidate artifacts only. A URL is a source reference, not an ingested source. `tools/source_snapshots.py` provides content-addressed immutable bytes and snapshot verification; `tools/build_candidate_queue.py` creates an operational queue from the frozen 18-candidate audit. None of the referenced sources has actually been captured in this execution. A source needs a retained snapshot, exact SHA-256, verified locator, version/date and applicable scope before review. Content hashing detects alteration; it does not establish agronomic correctness.

Lifecycle transitions are explicit: `RAW → PARSED → CANDIDATE → UNDER_REVIEW → APPROVED → PUBLISHED`. Rejection, return to candidate/review, and deprecation have explicit edges. Direct jumps are rejected. Approval requires distinct reviewer roles plus a separate qualified human action and external approval artifact; agent agreement is supporting evidence only. Each API transition emits a hash-linked event. `tools/knowledge_store.py` persists record changes and append-only events atomically in SQLite, with a compare-and-swap audit head and tamper checks. Actor authentication remains the caller's responsibility. A JSON starter store exists at `data/knowledge_base/approved_records.json` and is deliberately empty.

The approved knowledge store is canonical. FAISS files are disposable projections. `tools/build_knowledge_index.py` accepts only `PUBLISHED` records, validates the schema, requires a non-empty store, a local model and an explicit model manifest, and refuses to overwrite an existing index. `index_manifest.json` binds model ID/revision/dimension/artifact hash and knowledge release to the index file hashes. `LocalVectorDB` rejects unversioned or incompatible indexes. `tools.knowledge_release` creates a manifest bound to canonical records, source set, schema, corpus and index/policy versions. Hashes are integrity checks, not signatures or agronomic endorsements.

## Fields and versioning

Required record fields bind identity, revision, status, exact text/hash, at least one source reference, non-empty scope, timestamps, creator, approval slot and audit head. Context dimensions are optional keys in `scope` (crop, topic, region, state, municipality, climate, soil, production system, growth stage and season); they are not forced on every kind of record. Source edition/version, publication date, page/section, license, validity dates and snapshot details are optional until relevant. Schema, corpus, knowledge-base and retrieval-index versions are distinct.

## What exists / what remains

- Implemented and unit-tested: canonical record validation, content/source snapshot hashes, explicit source snapshot/locator contracts, status transitions, human review schema and hash binding, promotion blocker function, unresolved-disagreement records, tamper-detecting audit events, empty canonical store, release manifest contract, candidate-only Markdown CLI.
- Not yet implemented/operated: external identity and qualification verification, storing/acquiring real source bytes, license decisions, review UI, populated approved store, release signatures/rollback, complete platform-specific vector dependency lock, and a production index build.
- No candidate is promoted automatically. The legacy registry remains an independent fail-closed runtime gate; no record has been added to it.
