# Knowledge pipeline

Status: **DESIGN + structural implementation**. No agronomic record is approved or published. The machine-readable record contract is [`schemas/knowledge_record.schema.json`](schemas/knowledge_record.schema.json); Python validation and transition rules live in `tools/knowledge_schema.py` and `tools/knowledge_lifecycle.py`.

## Trust boundaries

```text
raw source snapshot → parse → candidate → review → human approval → published store → manifest → disposable index
```

`tools/ingest.py` and `tools/mining_agent.py` parse local Markdown into candidate artifacts only. A URL is a source reference, not an ingested source. To be approvable, every source must have a retained snapshot with an exact SHA-256, a locator, version/date and applicable scope. Content hashing detects alteration; it does not establish agronomic correctness.

Lifecycle transitions are explicit: `RAW → PARSED → CANDIDATE → UNDER_REVIEW → APPROVED → PUBLISHED`. Rejection, return to candidate/review, and deprecation have explicit edges. Direct jumps are rejected. Approval requires distinct reviewer roles plus a separate qualified human action and external approval artifact; agent agreement is supporting evidence only. Each API transition emits a hash-linked event. `tools/knowledge_store.py` persists record changes and append-only events atomically in SQLite, with a compare-and-swap audit head and tamper checks. Actor authentication remains the caller's responsibility. A JSON starter store exists at `data/knowledge_base/approved_records.json` and is deliberately empty.

The approved knowledge store is canonical. FAISS files are disposable projections. `tools/build_knowledge_index.py` accepts only `PUBLISHED` records, validates the schema, requires a non-empty store and refuses to overwrite an existing index. `tools/knowledge_release.py` creates a manifest bound to the canonical records hash, source set, schema, corpus and index/policy versions. Hashes are integrity checks, not signatures or agronomic endorsements.

## Fields and versioning

Required record fields bind identity, revision, status, exact text/hash, at least one source reference, non-empty scope, timestamps, creator, approval slot and audit head. Context dimensions are optional keys in `scope` (crop, topic, region, state, municipality, climate, soil, production system, growth stage and season); they are not forced on every kind of record. Source edition/version, publication date, page/section, license, validity dates and snapshot details are optional until relevant. Schema, corpus, knowledge-base and retrieval-index versions are distinct.

## What exists / what remains

- Implemented and unit-tested: canonical record validation, content/source snapshot hashes, status transitions, human review gates, tamper-detecting audit events, empty canonical store, release manifest contract, candidate-only Markdown CLI.
- Not yet implemented: authenticated operator identities, durable transactional append-only audit persistence, source acquisition/licensing workflow, a human review UI, populated approved store, release signatures/rollback and a production index build.
- No candidate is promoted automatically. The legacy registry remains an independent fail-closed runtime gate; no record has been added to it.
