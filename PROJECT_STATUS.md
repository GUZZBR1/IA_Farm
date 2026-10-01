# Project status

Current phase: Knowledge Engineering contracts, Golden Set governance and retrieval evaluation infrastructure. Baseline: `2c2082f304ba93531cfea2988946f622089f38ef`.

| Area | Current status | Evidence / limit |
|---|---|---|
| Runtime | Deterministic and fail-closed | Runtime curation registry is empty; no agronomic material is eligible. |
| Knowledge lifecycle | Local infrastructure implemented | Versioned record contract, lifecycle transitions, human approval checks, hash-linked events and transactional append-only SQLite persistence exist. Authenticated human identity remains external. |
| Canonical knowledge | Empty | `data/knowledge_base/approved_records.json` contains zero published records. No agricultural claim has been approved. |
| Candidate audit | Complete, not approval | All 18 drafts classified: 5 conflicting and 13 insufficient evidence. Zero are approved. |
| Retrieval | Lexical mechanics baseline | Synthetic non-agronomic dataset only. Approved corpus metrics are unavailable because the corpus is empty. |
| Vector dependencies | Must be probed in current environment | Prior validation reports are historical; current execution must report actual imports. No vector result is inferred from prior environments. |
| Behavioral simulations | Separate behavioral evidence | Historical 660/660 run is behavioral only; it does not validate retrieval or agronomy. |
| Android / SLM | Not started | Outside current phases and not validated. |

## Phase 3–5 work

Implemented: canonical JSON Schema and typed validation; explicit knowledge lifecycle; immutable-content/snapshot checks; hash-linked transition events with transactional append-only SQLite persistence; candidate-only parse CLIs; empty canonical store; publication manifest; published-only index builder; separate agronomic and synthetic retrieval sets; BM25 baseline; reproducible evaluation report; source-candidate audit; top-k metadata-filter expansion regression.

Validated only by tests and mechanics fixtures: schema/lifecycle invariants, filter aliases, token/accent mechanics, no-result behavior and candidate-window expansion. No agricultural truth is inferred by these results.

Not validated: actual source snapshots/licenses; any Golden Set case; semantic vector quality; retrieval thresholds; hybrid superiority; real FAISS execution in this environment unless dependency probe succeeds; authenticated operator identity.

## Historical evidence

The earlier status documents report a 9-vector FAISS smoke and 660 behavioral simulation runs from their dated environments. They remain historical records, not current reruns or agronomic accuracy claims. A previous review comparison field `human_approval_required:false` is superseded; qualified human approval plus source snapshots are required now.

## Remaining risks

- Legacy corn MVP docs contain unverified example claims and must not be ingested as approved knowledge.
- Knowledge transition APIs return record/event pairs; durable atomic append-only persistence and authenticated human identity still need an implementation before production use.
- Source licenses, immutable source acquisition, validity review and professional approval remain outstanding.
- Retrieval has no approved query-record labels; threshold and model comparisons are unscored.
