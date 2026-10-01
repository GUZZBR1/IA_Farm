# Project status

Current phase: Source acquisition and human-review operations, vector runtime reproducibility, Context Engine preparation. Starting baseline: `9e890f57864c954d7d394cfe1297fa77026df46e`.

| Area | Current status | Evidence / limit |
|---|---|---|
| Runtime | Deterministic and fail-closed | Runtime curation registry is empty; no agronomic material is eligible. |
| Knowledge lifecycle | Local infrastructure implemented | Versioned record contract, lifecycle transitions, human approval checks, hash-linked events and transactional append-only SQLite persistence exist. Authenticated human identity remains external. |
| Canonical knowledge | Empty | `data/knowledge_base/approved_records.json` contains zero published records. No agricultural claim has been approved. |
| Candidate audit | Complete, not approval | All 18 drafts classified: 5 conflicting and 13 insufficient evidence. Zero are approved. |
| Retrieval | Lexical mechanics baseline | Synthetic non-agronomic dataset only. Approved corpus metrics are unavailable because the corpus is empty. |
| Source acquisition | Operational queue + snapshot code | 18/18 source references; 0 retained snapshots; no URL was refreshed in this phase. |
| Human review | Hash-bound review/gate structures | 0 review-ready packets; 5 unresolved AI-review disagreements are not confirmed source contradictions. |
| Vector dependencies | `DEPENDENCY_MISSING` in current WSL | NumPy imports in system Python; FAISS, Sentence-Transformers, Torch and Transformers missing. WSL PyPI DNS fails; target wheel compatibility is plausible, complete install not verified. |
| Retrieval evaluation | BM25 synthetic baseline only | Vector blocked; hybrid not run; approved corpus has zero records. |
| Context | Design matrix documented | Candidate metadata only; requirements are not yet qualified or integrated into runtime. |
| Behavioral simulations | Separate behavioral evidence | Current rerun: 660/660 persona runs pass; behavioral only, not retrieval or agronomic validation. |
| Android / SLM | Not started | Outside current phases and not validated. |

## Prior phases 3–5 (not repeated)

Implemented: canonical JSON Schema and typed validation; explicit knowledge lifecycle; immutable-content/snapshot checks; hash-linked transition events with transactional append-only SQLite persistence; candidate-only parse CLIs; empty canonical store; publication manifest; published-only index builder; separate agronomic and synthetic retrieval sets; BM25 baseline; reproducible evaluation report; source-candidate audit; top-k metadata-filter expansion regression.

Validated only by tests and mechanics fixtures: schema/lifecycle invariants, filter aliases, token/accent mechanics, no-result behavior and candidate-window expansion. No agricultural truth is inferred by these results.

## Current phase work

Implemented: source snapshot/locator/license contracts; immutable content-addressed storage; 18-row operational candidate queue; five unresolved disagreement records; hash-bound human review and promotion gate; explicit vector capability diagnostics and index compatibility manifest; model downloads disabled; core/vector dependency profiles; initial Context Engine requirements; workflow challenge scenarios.

Validated: 110 unit/contract tests pass in WSL; candidate queue regenerates at 18 total (13 snapshot/evidence-insufficient, 5 unresolved AI-review disagreements, 0 ready); registry validation passes with zero entries; compile and security scan pass; 660/660 behavioral simulations pass. BM25 synthetic-only run reports Recall@3 1.0, Precision@3 0.667, MRR 1.0, no-result accuracy 1.0, wrong-region rate 0.0, forbidden-source rate 0.0, and mean latency 0.155 ms on WSL. No source bytes were captured; no review packet can be marked ready; no agricultural claim has been approved.

Not validated: actual source license, snapshot locator or agronomic claim; full vector dependency resolution/install; local model artifact; vector retrieval scores, hybrid comparison, context behavior in production runtime, or authenticated reviewer identity.

## Historical evidence

The earlier status documents report a 9-vector FAISS smoke and 660 behavioral simulation runs from their dated environments. They remain historical records, not current reruns or agronomic accuracy claims. A previous review comparison field `human_approval_required:false` is superseded; qualified human approval plus source snapshots are required now.

## Remaining risks

- Legacy corn MVP docs contain unverified example claims and must not be ingested as approved knowledge.
- External source acquisition, rights verification and qualified professional approval remain outstanding.
- `requirements-vector.in` pins direct packages only; a complete target-platform transitive lock remains necessary before install reproducibility can be claimed.
- Retrieval has no approved query-record labels; vector/hybrid, threshold, and agronomic accuracy are unscored.
- Runtime authorization binds retrieval scope to the validated frozen review scope and checks source validity dates; risk-tier-specific reviewer counts remain a documented design proposal and are not yet enforced.
